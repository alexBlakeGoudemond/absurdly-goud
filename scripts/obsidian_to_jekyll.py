#!/usr/bin/env python3
"""Obsidian -> Jekyll exporter (improved).

Goals:
- Keep the vault content-only (Markdown, attachments). The exporter injects Jekyll templates,
  front-matter, and fixes links to produce a buildable site_src.
- Copy repo templates/includes/assets into site_src so the vault doesn't need Jekyll files.
- Normalize _posts filenames to include YYYY-MM-DD prefix when missing (uses front-matter date or mtime).
- Convert wikilinks and image links to Markdown links pointing at the generated HTML pages or copied assets.
- Remove any pre-existing HTML files from the exported tree.

Stdlib-only so it runs in GitHub Actions without extra deps.
"""

import argparse
from pathlib import Path
import shutil
import re
import os
import json
from datetime import datetime

WIKILINK_RE = re.compile(r"!\?\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
DATE_IN_FM = re.compile(r"^date:\s*(.+)", re.IGNORECASE)


def slugify(s: str):
    s = s.strip().lower()
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"[^a-z0-9\-]", "", s)
    return s


def copy_vault(vault: Path, out: Path):
    if out.exists():
        shutil.rmtree(out)

    def ignore_fn(directory, names):
        ignored = set()
        for n in names:
            if n == '.obsidian' or n == '.git':
                ignored.add(n)
            # avoid following absolute symlinks (ai-playbook)
            if n == '.ai-playbook':
                ignored.add(n)
        return ignored

    shutil.copytree(vault, out, ignore=ignore_fn)


def copy_repo_templates(repo_root: Path, out: Path):
    # Copy _layouts, _includes, assets, media into out
    for name in ["_layouts", "_includes", "assets", "media", "_sass"]:
        src = repo_root / name
        if src.exists():
            dst = out / name
            # use copytree with dirs_exist_ok when available
            try:
                shutil.copytree(src, dst, dirs_exist_ok=True)
            except TypeError:
                # older shutil without dirs_exist_ok
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)


def read_front_matter_date(text: str):
    # very small parser: look for 'date:' in top YAML block
    if text.lstrip().startswith('---'):
        parts = text.split('---', 2)
        if len(parts) >= 2:
            fm = parts[1]
            for line in fm.splitlines():
                m = DATE_IN_FM.match(line.strip())
                if m:
                    # try parse date
                    try:
                        return datetime.fromisoformat(m.group(1).strip())
                    except Exception:
                        try:
                            return datetime.strptime(m.group(1).strip(), '%Y-%m-%d %H:%M:%S')
                        except Exception:
                            return None
    return None


def ensure_front_matter(md_path: Path, ensure_layout: str = None, title_override: str = None):
    txt = md_path.read_text(encoding='utf8')
    if txt.lstrip().startswith('---'):
        # optionally ensure layout exists
        if ensure_layout:
            # naive insertion if layout missing
            if 'layout:' not in txt.split('---', 2)[1]:
                parts = txt.split('---', 2)
                parts[1] = parts[1].strip() + f"\nlayout: {ensure_layout}\n"
                md_path.write_text('---' + parts[1] + '---' + (parts[2] if len(parts) > 2 else ''), encoding='utf8')
        return
    # find first heading
    title = None
    for line in txt.splitlines():
        s = line.strip()
        if s.startswith('#'):
            title = s.lstrip('#').strip()
            break
    if not title:
        title = md_path.stem
    if title_override:
        title = title_override
    mtime = datetime.fromtimestamp(md_path.stat().st_mtime)
    date = mtime.strftime('%Y-%m-%d %H:%M:%S')
    fm = f"---\ntitle: \"{title}\"\ndate: {date}\n"
    if ensure_layout:
        fm += f"layout: {ensure_layout}\n"
    fm += "---\n\n"
    md_path.write_text(fm + txt, encoding='utf8')


def find_target_file(out: Path, name: str):
    """Search the exported out tree for a file matching name (case-insensitive, ignoring extension)."""
    # exact match first
    candidates = list(out.rglob(name + '.*'))
    if candidates:
        return candidates[0]
    lower = name.lower()
    for p in out.rglob('*'):
        if p.is_file() and p.stem.lower() == lower:
            return p
    return None


def convert_wikilinks_in_text(text: str, src_file: Path, out: Path):
    def repl(m):
        target = m.group(1).strip()
        alias = m.group(2)
        is_image = text[m.start()] == '!'
        display = alias.strip() if alias else target
        tgt = find_target_file(out, target)
        if tgt:
            rel = Path(os.path.relpath(tgt, out))
            # If target is markdown, link to .html
            if tgt.suffix.lower() in ['.md', '.markdown']:
                rel_out = rel.with_suffix('.html')
            else:
                rel_out = rel
            # compute relative URL from src_file in out
            try:
                src_rel = Path(os.path.relpath(src_file, out))
                url = Path(os.path.relpath(rel_out, start=src_rel.parent)).as_posix()
            except Exception:
                url = rel_out.as_posix()
            if is_image:
                return f'![{display}]({url})'
            else:
                return f'[{display}]({url})'
        else:
            slug = slugify(target)
            if is_image:
                return f'![{display}]({slug})'
            return f'[{display}]({slug})'
    return WIKILINK_RE.sub(repl, text)


def process_markdown_files(out: Path):
    for md in out.rglob('*.md'):
        # ensure front matter (use default layout if present)
        ensure_front_matter(md, ensure_layout='default')
        text = md.read_text(encoding='utf8')
        new_text = convert_wikilinks_in_text(text, md, out)
        if new_text != text:
            md.write_text(new_text, encoding='utf8')


def normalize_posts(out: Path):
    posts_root = out / '_posts'
    if not posts_root.exists():
        return
    for md in posts_root.rglob('*.md'):
        stem = md.stem
        # if starts with YYYY-MM-DD, skip
        if re.match(r'^\d{4}-\d{2}-\d{2}', stem):
            continue
        txt = md.read_text(encoding='utf8')
        dt = read_front_matter_date(txt)
        if not dt:
            dt = datetime.fromtimestamp(md.stat().st_mtime)
        date_str = dt.strftime('%Y-%m-%d')
        new_name = f"{date_str}-{slugify(stem)}.md"
        new_path = md.with_name(new_name)
        # if collision, append a counter
        i = 1
        while new_path.exists():
            new_path = md.with_name(f"{date_str}-{slugify(stem)}-{i}.md")
            i += 1
        md.rename(new_path)


def remove_html_files(out: Path):
    for h in out.rglob('*.html'):
        try:
            h.unlink()
        except Exception:
            pass


def sync_to_repo(temp_out: Path, repo_root: Path):
    """Copy processed files from temp_out into the repo's Jekyll locations.
    This overwrites files in the working tree but does not commit.
    """
    # ensure dirs
    (repo_root / '_posts').mkdir(parents=True, exist_ok=True)
    (repo_root / 'about').mkdir(parents=True, exist_ok=True)
    (repo_root / '_includes').mkdir(parents=True, exist_ok=True)
    (repo_root / 'media').mkdir(parents=True, exist_ok=True)
    (repo_root / 'assets').mkdir(parents=True, exist_ok=True)

    # copy posts: replace repo _posts with vault posts
    dst_posts_root = repo_root / '_posts'
    if dst_posts_root.exists():
        shutil.rmtree(dst_posts_root)
    src_posts = temp_out / '_posts'
    if src_posts.exists():
        for p in src_posts.rglob('*'):
            if p.is_file():
                rel = p.relative_to(src_posts)
                dst = repo_root / '_posts' / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, dst)

    # process about: create an include fragment from vault about content and write repo/about/index.md wrapper
    src_about = temp_out / 'about'
    about_fragment = None
    if src_about.exists():
        # prefer about/index.md or about/about.md or first md inside about/
        candidates = [src_about / 'index.md', src_about / 'about.md']
        for c in candidates:
            if c.exists():
                about_fragment = c
                break
        if not about_fragment:
            md_files = list(src_about.rglob('*.md'))
            if md_files:
                about_fragment = md_files[0]
        if about_fragment:
            includes_dir = repo_root / '_includes'
            includes_dir.mkdir(parents=True, exist_ok=True)
            dst_inc = includes_dir / 'about_fragment.md'
            shutil.copy2(about_fragment, dst_inc)
            print(f'Copied about fragment to {dst_inc}')
            # write wrapper at repo/about/index.md
            about_dir = repo_root / 'about'
            about_dir.mkdir(parents=True, exist_ok=True)
            index_about = about_dir / 'index.md'
            fm = "---\nlayout: default\ntitle: About\npermalink: /about/\n---\n\n"
            include_line = "{% include about_fragment.md %}\n"
            index_about.write_text(fm + include_line, encoding='utf8')
            print(f'Wrote repo about wrapper at {index_about}')
    else:
        # no about in vault; leave existing repo about alone
        pass

    # copy media and assets
    for name in ['media', 'assets']:
        src = temp_out / name
        if src.exists():
            for p in src.rglob('*'):
                if p.is_file():
                    rel = p.relative_to(src)
                    dst = repo_root / name / rel
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(p, dst)

    # Determine home candidate (where vault keeps the home content)
    # Prefer vault/home/home.md (or home/index.md) as the site home source
    home_candidates = [
        temp_out / 'home' / 'home.md',
        temp_out / 'home' / 'index.md',
        temp_out / 'index.md',
        temp_out / 'home.md',
        temp_out / 'index_fragment.md',
    ]
    home_src = None
    for c in home_candidates:
        if c.exists():
            home_src = c
            break

    # If we found a home source, write it to repo_root/index.md with infra h-card prepended
    if home_src:
        txt = home_src.read_text(encoding='utf8')
        body = txt
        title = 'Home'
        if txt.lstrip().startswith('---'):
            parts = txt.split('---', 2)
            if len(parts) >= 3:
                fm_block = parts[1]
                body = parts[2]
                for line in fm_block.splitlines():
                    if line.strip().lower().startswith('title:'):
                        title = line.split(':', 1)[1].strip().strip('\"\'')
                        break
        index_root = repo_root / 'index.md'
        fm = "---\nlayout: default\n"
        if title:
            fm += f"title: \"{title}\"\n"
        fm += "---\n\n"
        hcard = (
            '<div class="h-card">\n'
            '    <p class="p-name">\n'
            '        Alex Blake-Goudemond\n'
            '    </p>\n\n'
            '    <a class="u-url"\n'
            '       href="https://alexblakegoudemond.com"\n'
            '       rel="me">\n'
            '        alexblakegoudemond.com\n'
            '    </a>\n\n'
            '    <a class="u-url"\n'
            '       href="https://absurdlygoud.com">\n'
            '        absurdlygoud.com\n'
            '    </a>\n\n'
            '    <a class="u-url"\n'
            '       href="https://github.com/alexBlakeGoudemond"\n'
            '       rel="me">\n'
            '        GitHub\n'
            '    </a>\n'
            '</div>\n\n'
        )
        # copy home source into _includes as a fragment and create a root index.md that includes it
        includes_dir = repo_root / '_includes'
        includes_dir.mkdir(parents=True, exist_ok=True)
        dst_inc = includes_dir / 'home_fragment.md'
        shutil.copy2(home_src, dst_inc)
        print(f'Copied home fragment to {dst_inc}')
        index_root.write_text(fm + hcard + "{% include home_fragment.md %}\n", encoding='utf8')
        print(f'Wrote root index.md at {index_root} (includes home_fragment.md)')

    # copy other top-level markdown pages (except the home_src which we've handled)
    for p in temp_out.glob('*.md'):
        if home_src and p.samefile(home_src):
            continue
        dst = repo_root / p.name
        shutil.copy2(p, dst)

    # copy other directories (pages) at top-level, excluding special dirs
    skip_dirs = {'_posts', 'about', 'media', 'assets', '_includes', '.obsidian', 'home'}
    for d in temp_out.iterdir():
        if d.is_dir() and d.name not in skip_dirs:
            # copy contents into repo root/d
            for p in d.rglob('*'):
                if p.is_file():
                    rel = p.relative_to(d)
                    dst = repo_root / d.name / rel
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(p, dst)


def main():
    p = argparse.ArgumentParser(description='Export Obsidian vault to a Jekyll-friendly source tree and write into repo or output dir')
    p.add_argument('--vault', default='absurdly-goud-obsidian')
    p.add_argument('--out-root', default='.')
    p.add_argument('--out', default=None, help='If provided, generate the site source into this directory and do NOT sync into the repo')
    args = p.parse_args()

    vault = Path(args.vault)
    repo_root = Path(args.out_root)
    out_dir = args.out

    if not vault.exists():
        print(f'Vault path {vault} does not exist. Nothing to do.')
        return

    repo_root = Path(__file__).resolve().parents[1] if repo_root == Path('.') else repo_root

    if out_dir:
        # generate-only mode: write processed site source into out_dir and exit
        out = Path(out_dir)
        if out.exists():
            shutil.rmtree(out)
        print(f'Generating site source from {vault} -> {out}')
        copy_vault(vault, out)
        print('Copying repo templates/includes/assets into output')
        copy_repo_templates(repo_root, out)
        print('Removing pre-generated HTML files (keep source only)')
        remove_html_files(out)
        print('Normalizing posts filenames')
        normalize_posts(out)
        print('Processing markdown files (front-matter, wikilinks)')
        process_markdown_files(out)
        print('Generation complete.')
        return

    # Default behavior: sync processed content into repo root
    temp_out = repo_root / '.obsidian_export_tmp'
    if temp_out.exists():
        shutil.rmtree(temp_out)

    print(f'Copying vault {vault} -> {temp_out}')
    copy_vault(vault, temp_out)

    print('Removing pre-generated HTML files (keep source only)')
    remove_html_files(temp_out)

    print('Normalizing posts filenames')
    normalize_posts(temp_out)

    print('Processing markdown files (front-matter, wikilinks)')
    process_markdown_files(temp_out)

    print('Syncing processed content into repository root')
    sync_to_repo(temp_out, repo_root)

    # cleanup
    try:
        shutil.rmtree(temp_out)
    except Exception:
        pass

    print('Export complete.')


if __name__ == '__main__':
    main()
