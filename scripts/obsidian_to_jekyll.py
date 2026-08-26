#!/usr/bin/env python3

import argparse
from pathlib import Path
import shutil
import re
from textwrap import dedent

from scripts.website_manifest import (
    sha256,
    create_manifest_entry,
    load_manifest,
    save_manifest,
)

MANIFEST_FILENAME = ".manifest.json"

MARKDOWN_FENCE_PATTERN = re.compile(r'^(\s*)(```|~~~)(\S*)\s*$')
MARKDOWN_IMAGE_PATTERN = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')
MARKDOWN_INLINE_CODE_PATTERN = re.compile(r'`[^`]*`')

# Matches Obsidian wikilinks: [[NoteName#NoteSubSection|AltText]]
# Both #NoteSubSection and |AltText are optional.
WIKILINK_PATTERN = re.compile(
    r"""
    \[\[
        (?P<note>[^\]#|]+)             # NoteName            (required)
        (?: \# (?P<section>[^\]|]+) )? # #NoteSubSection     (optional)
        (?: \| (?P<alt>[^\]]+) )?      # |AltText            (optional)
    \]\]
    """,
    re.VERBOSE,
)


def build_note_path_lookup(root: Path) -> dict[str, str]:
    """
    Scans `root` (the OUTPUT tree, i.e. self.output_location, not the vault)
    and builds a lookup of note name -> path relative to root, using forward
    slashes so it can be dropped straight into a {% link %} tag.

    Must run against the output tree because copy_vault_resources() renames
    the vault's posts/ folder to _posts/ on the way out — resolving against
    the vault would produce links pointing at a path that no longer exists.

    Assumes note names are unique across the vault, mirroring how Obsidian
    itself resolves [[wikilinks]] (by basename, regardless of folder).
    """
    lookup: dict[str, str] = {}

    for md_file in root.rglob("*.md"):
        note_name = md_file.stem
        relative_path = md_file.relative_to(root).as_posix()

        if note_name in lookup:
            raise ValueError(
                f"Duplicate note name '{note_name}' found at both "
                f"'{lookup[note_name]}' and '{relative_path}'. "
                "Wikilink resolution requires unique note names across the site."
            )

        lookup[note_name] = relative_path

    return lookup


def convert_markdown_syntax_to_jekyll_syntax(markdown_file: Path, note_path_lookup: dict[str, str]) -> None:
    process_markdown_for_jekyll(markdown_file, note_path_lookup)


def process_markdown_for_jekyll(markdown_file: Path, note_path_lookup: dict[str, str]) -> None:
    """Convert Obsidian-style notations to formats that Jekyll recognizes"""
    print(f"processing markdown for '{markdown_file.name}'")
    content = markdown_file.read_text(encoding="utf-8")
    # Wikilinks first, while the raw ``` fences are still intact, so example
    # wikilinks inside code samples/inline code can be skipped rather than
    # resolved as if they were real links.
    new_content = convert_wikilinks_outside_code(content, note_path_lookup)
    new_content = escape_markdown_codeblocks_for_jekyll(new_content)
    if new_content != content:
        markdown_file.write_text(new_content, encoding="utf-8")


def convert_wikilinks_outside_code(content: str, note_path_lookup: dict[str, str]) -> str:
    """
    Applies convert_wikilinks_to_jekyll_layout only to text outside fenced '```'
    code blocks and inline `code` spans, mirroring how images are already
    kept out of code regions. Without this, a documentation example like
    `` `[[...]]` `` or a ```markdown sample containing [[Note]] gets treated
    as a real link and fails lookup.
    """
    lines = content.split('\n')
    output_lines = []
    in_fence = False
    fence_marker = None

    for line in lines:
        fence_match = MARKDOWN_FENCE_PATTERN.match(line)
        if fence_match:
            marker = fence_match.group(2)
            if not in_fence:
                in_fence = True
                fence_marker = marker
            elif marker == fence_marker:
                in_fence = False
            output_lines.append(line)
            continue

        if in_fence:
            output_lines.append(line)
        else:
            output_lines.append(convert_wikilinks_in_line_outside_inline_code(line, note_path_lookup))

    return '\n'.join(output_lines)


def convert_wikilinks_in_line_outside_inline_code(line: str, note_path_lookup: dict[str, str]) -> str:
    """Converts wikilinks on a single line, skipping anything inside `inline code` spans."""
    segments = []
    last_end = 0
    for code_match in MARKDOWN_INLINE_CODE_PATTERN.finditer(line):
        segments.append(convert_wikilinks_to_jekyll_layout(line[last_end:code_match.start()], note_path_lookup))
        segments.append(code_match.group(0))  # leave inline code untouched
        last_end = code_match.end()
    segments.append(convert_wikilinks_to_jekyll_layout(line[last_end:], note_path_lookup))
    return ''.join(segments)


def slugify(text: str) -> str:
    """Mimics kramdown's auto-generated heading anchors: lowercase, spaces to hyphens."""
    return text.strip().lower().replace(" ", "-")


def convert_wikilinks_to_jekyll_layout(content: str, note_path_lookup: dict[str, str]) -> str:
    """
    Converts Obsidian-style wikilinks into a Jekyll {% link %} layout, resolving
    each note name to its real path in the output tree via note_path_lookup
    (see build_note_path_lookup).

    [[Note]]                       -> [Note]({% link path/to/Note.md %})
    [[Note#Sub Section]]           -> [Note]({% link path/to/Note.md %}#sub-section)
    [[Note|Alt Text]]              -> [Alt Text]({% link path/to/Note.md %})
    [[Note#Sub Section|Alt Text]]  -> [Alt Text]({% link path/to/Note.md %}#sub-section)
    """

    def replace(match: re.Match) -> str:
        note, section, alt = match.groupdict().values()
        note = note.strip()

        try:
            note_path = note_path_lookup[note]
        except KeyError:
            raise ValueError(
                f"Wikilink references unknown note '{note}'. "
                "Check the note exists in the vault/output tree and the lookup is current."
            ) from None

        link_text = alt.strip() if alt else note
        anchor = f"#{slugify(section)}" if section else ""

        return f"[{link_text}]({{% link {note_path} %}}{anchor})"

    return WIKILINK_PATTERN.sub(replace, content)


def escape_markdown_codeblocks_for_jekyll(content: str) -> str:
    lines = content.split('\n')
    output_lines = []
    in_fence = False
    fence_marker = None

    for line in lines:
        fence_match = MARKDOWN_FENCE_PATTERN.match(line)
        if fence_match:
            marker = fence_match.group(2)
            if not in_fence:
                in_fence = True
                fence_marker = marker
                output_lines.append('{% raw %}')
                output_lines.append(line)
            elif marker == fence_marker:
                in_fence = False
                output_lines.append(line)
                output_lines.append('{% endraw %}')
            else:
                output_lines.append(line)
            continue

        if in_fence:
            output_lines.append(line)
        else:
            output_lines.append(convert_images_outside_inline_code(line))

    return '\n'.join(output_lines)


def convert_images_outside_inline_code(line: str) -> str:
    """Convert image syntax on a line, skipping anything inside `inline code` spans."""
    segments = []
    last_end = 0
    for code_match in MARKDOWN_INLINE_CODE_PATTERN.finditer(line):
        segments.append(replace_images_in_segment(line[last_end:code_match.start()]))
        segments.append(code_match.group(0))  # leave inline code untouched
        last_end = code_match.end()
    segments.append(replace_images_in_segment(line[last_end:]))
    return ''.join(segments)


def replace_images_in_segment(segment: str) -> str:
    def replace(match: re.Match) -> str:
        image_alt_text = match.group(1)
        image_name = match.group(2)
        return convert_markdown_image_notation_to_jekyll_includes_image_notation(
            image_name, image_alt_text
        )

    return MARKDOWN_IMAGE_PATTERN.sub(replace, segment)


def convert_markdown_image_notation_to_jekyll_includes_image_notation(image_name: str, image_alt_text: str) -> str:
    opening_brace = '{%'
    closing_brace = '%}'
    jekyll_image_layout_notation = f"""
        {opening_brace} include image.html
            src="{image_name}"
            alt="{image_alt_text}"
            title="{image_alt_text}"
        {closing_brace}
        """
    return dedent(jekyll_image_layout_notation)


class ObsidianToJekyllConverter:
    """Syncs an Obsidian vault + Jekyll scaffold into a Jekyll-ready source tree,
    using a content-hash manifest to skip unchanged files on repeat runs."""

    IGNORED_VAULT_ITEMS = ['.obsidian', 'website-whiteboard.excalidraw']
    INCLUDED_JEKYLL_ITEMS = ['assets', 'CNAME', 'posts', '_includes', '_layouts', '_config.yaml', 'index.md', '_data']
    IGNORED_FRONTMATTER_FILES = ['index.md', 'home.md']
    PERMALINK_FILES = ['about.md', 'vision.md']

    def __init__(self, obsidian_vault_location: Path, output_location: Path, source_location: Path):
        self.obsidian_vault_location = obsidian_vault_location
        self.output_location = output_location
        self.source_location = source_location
        self.manifest_path = output_location / MANIFEST_FILENAME

        self.old_manifest: dict = {}
        self.new_manifest: dict = {}
        self.changed_dest_paths: list[Path] = []

    def begin_run(self) -> None:
        """Load the on-disk manifest and reset per-run tracking state.
        Called at the start of run(), and reusable directly in tests
        to simulate a second, separate invocation of the converter."""
        self.old_manifest = load_manifest(self.manifest_path)
        self.new_manifest = {}
        self.changed_dest_paths = []

    def run(self) -> None:
        if not self.obsidian_vault_location.exists():
            print(f"Vault path '{self.obsidian_vault_location}' does not exist. Requires vault to be present.")
            return

        self.output_location.mkdir(parents=True, exist_ok=True)
        self.begin_run()

        self.copy_vault_resources()
        self.copy_jekyll_resources()
        self.copy_vault_images_into_assets_directory()

        # Built AFTER all copying so it reflects the final output tree
        # (e.g. posts/ -> _posts/), and covers every note, not just
        # the ones changed this run, since an unchanged note may still
        # be a valid wikilink target for a changed one.
        note_path_lookup = build_note_path_lookup(self.output_location)

        self.parse_markdown_files_for_jekyll(note_path_lookup)
        self.prune_stale_files()
        save_manifest(self.manifest_path, self.new_manifest)

    def sync_file(self, source_path: Path, dest_path: Path) -> None:
        """Copy source_path to dest_path only if content changed since last run.
        Manifest is keyed by SOURCE path so renames (same source, new dest) are detectable."""
        source_key = str(source_path)
        current_hash = sha256(source_path)
        old_entry = self.old_manifest.get(source_key)

        # has a rename/move occurred?
        if old_entry and old_entry["dest"] != str(dest_path):
            stale_path = Path(old_entry["dest"])
            if stale_path.exists():
                print(f"Removing stale (renamed) file: '{stale_path}'")
                stale_path.unlink()
            old_entry = None

        # are the contents unchanged?
        if old_entry and old_entry["sha256"] == current_hash and dest_path.exists():
            self.new_manifest[source_key] = old_entry
            return

        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, dest_path)
        print(f"Synced (changed): '{source_path}' -> '{dest_path}'")
        self.new_manifest[source_key] = create_manifest_entry(source_path, dest_path)
        self.changed_dest_paths.append(dest_path)

    def sync_tree(self, source_dir: Path, dest_dir: Path, exclude_suffixes: set[str] = frozenset()) -> None:
        """Walk source_dir recursively, syncing each file individually."""
        for source_path in source_dir.rglob("*"):
            if source_path.is_dir():
                continue
            if source_path.suffix.lower() in exclude_suffixes:
                continue
            relative = source_path.relative_to(source_dir)
            self.sync_file(source_path, dest_dir / relative)

    def prune_stale_files(self) -> None:
        """Delete any output file whose source no longer exists in the new manifest."""
        stale_keys = self.old_manifest.keys() - self.new_manifest.keys()
        for source_key in stale_keys:
            stale_path = Path(self.old_manifest[source_key]["dest"])
            if stale_path.exists():
                print(f"Removing stale file: '{stale_path}'")
                stale_path.unlink()

    def copy_vault_images_into_assets_directory(self) -> None:
        output_image_path = self.output_location / 'assets/images/'
        output_image_path.mkdir(parents=True, exist_ok=True)
        for image_file in self.obsidian_vault_location.rglob('*.png'):
            self.sync_file(image_file, output_image_path / image_file.name)

    def parse_markdown_files_for_jekyll(self, note_path_lookup: dict[str, str]) -> None:
        """Only inject frontmatter into files actually (re)written this run —
        prevents double-prepending frontmatter onto cache-hit files."""
        for dest_path in self.changed_dest_paths:
            if dest_path.suffix != '.md':
                continue

            if dest_path.name in self.IGNORED_FRONTMATTER_FILES:
                print(f"Skipping adding of frontmatter to '{dest_path.name}'")
            elif dest_path.name in self.PERMALINK_FILES:
                self.add_frontmatter_to_file(dest_path, include_permalink=True)
            else:
                self.add_frontmatter_to_file(dest_path)

            convert_markdown_syntax_to_jekyll_syntax(dest_path, note_path_lookup)

    @staticmethod
    def add_frontmatter_to_file(markdown_file: Path, file_layout='default', include_permalink=False) -> None:
        file_title = ObsidianToJekyllConverter.extract_title_from_file_name(markdown_file.name)
        file_content = markdown_file.read_text(encoding="utf-8")
        file_permalink = f"/{file_title}/" if include_permalink else ""

        frontmatter = dedent(f"""
            ---
            layout: {file_layout}
            title: "{file_title}"
            permalink: {file_permalink}
            ---

        """).lstrip('\n')
        if 'permalink: \n' in frontmatter:
            frontmatter = frontmatter.replace('permalink: \n', '')
        markdown_file.write_text(frontmatter + file_content, encoding="utf-8")

    @staticmethod
    def extract_title_from_file_name(file_name: str) -> str:
        filename_with_leading_timestamp = re.compile(r'^\d{4}-\d{2}-\d{2}-')
        filename_ending_in_md = re.compile(r'\.md$')
        file_title = filename_with_leading_timestamp.sub('', file_name)
        file_title = filename_ending_in_md.sub('', file_title)
        return file_title

    def copy_jekyll_resources(self) -> None:
        for source_item in self.source_location.iterdir():
            if source_item.name not in self.INCLUDED_JEKYLL_ITEMS:
                continue
            dest_path = self.output_location / source_item.name
            if source_item.is_dir():
                self.sync_tree(source_item, dest_path)
            else:
                self.sync_file(source_item, dest_path)

    def copy_vault_resources(self) -> None:
        for vault_item in self.obsidian_vault_location.iterdir():
            if vault_item.name in self.IGNORED_VAULT_ITEMS:
                continue
            if vault_item.name == 'posts':
                image_suffixes = {'.png', '.jpg', '.jpeg', '.gif'}
                self.sync_tree(vault_item, self.output_location / '_posts', exclude_suffixes=image_suffixes)
            else:
                self.sync_tree(vault_item, self.output_location / vault_item.name)


def extract_command_line_arguments(args: argparse.Namespace) -> tuple[Path, Path, Path]:
    obsidian_vault_location = Path(args.vault)
    output_location = Path(args.out_dir)
    if args.src_root == Path("."):
        source_location = Path(__file__).resolve().parents[1]
    else:
        source_location = Path(args.src_root)
    return obsidian_vault_location, output_location, source_location


def main():
    argument_parser = argparse.ArgumentParser(
        description='Export Obsidian vault to a Jekyll-friendly source tree and write into repo or output dir')
    argument_parser.add_argument('--vault', default='absurdly-goud-obsidian')
    argument_parser.add_argument('--src-root', default='.')
    argument_parser.add_argument('--out-dir', default='site_src',
                                 help='If provided, generate the site source into this directory and do NOT sync into the repo')
    arguments = argument_parser.parse_args()

    obsidian_vault_location, output_location, source_location = extract_command_line_arguments(arguments)
    converter = ObsidianToJekyllConverter(obsidian_vault_location, output_location, source_location)
    converter.run()


if __name__ == '__main__':
    main()