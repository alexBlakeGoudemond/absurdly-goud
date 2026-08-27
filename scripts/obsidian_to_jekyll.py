#!/usr/bin/env python3
"""
ENTRYPOINT. CLI argument handling + ObsidianToJekyllConverter: orchestrates
syncing an Obsidian vault and Jekyll scaffold into a Jekyll-ready source tree.

This module should only ever coordinate the pieces below — the actual
conversion/sync logic lives in the imported modules, so each stays testable
and understandable on its own.
"""

import argparse
from pathlib import Path

from scripts.codeblock_escaping import escape_markdown_codeblocks_for_jekyll
from scripts.excalidraw_embeds import is_excalidraw_note, swap_excalidraw_note_with_image_embed
from scripts.filenames import slugify_filename
from scripts.jekyll_frontmatter import add_frontmatter_to_file
from scripts.markdown_images import convert_images_outside_code, convert_wikilink_image_embeds_outside_code
from scripts.site_sync import SiteSync
from scripts.wikilinks import build_note_path_lookup, convert_wikilinks_outside_code

MANIFEST_FILENAME = ".manifest.json"


def process_markdown_for_jekyll(markdown_file: Path, note_path_lookup: dict[str, str]) -> None:
    """Convert Obsidian-style notations to formats that Jekyll recognizes"""
    print(f"processing markdown for '{markdown_file.name}'")
    content = markdown_file.read_text(encoding="utf-8")
    # Obsidian's own `![[image.png]]` embed syntax is normalized to standard
    # `![alt](src)` markdown FIRST, before wikilinks run — otherwise a `[[...]]`
    # preceded by `!` gets mistaken for a note link by the wikilink pattern
    # and fails lookup (it's an image filename, not a note).
    new_content = convert_wikilink_image_embeds_outside_code(content)
    new_content = convert_wikilinks_outside_code(new_content, note_path_lookup)
    new_content = convert_images_outside_code(new_content)
    new_content = escape_markdown_codeblocks_for_jekyll(new_content)
    if new_content != content:
        markdown_file.write_text(new_content, encoding="utf-8")


def find_section(dest_path: Path, section_folders: list[str]) -> str | None:
    """
    Returns the entry in `section_folders` that `dest_path` lives under, if
    any (searches all ancestors). For example, each of the files below will
    be part of the section `vision`:
    ```
    |-- vision/
        |-- design/
            |-- website-design.md
            |-- website-inspiration.md
        |-- progress/
            |-- website-progress.md
        |-- whiteboard/
            |-- website-whiteboard.excalidraw.md
    ```
    """
    for part in dest_path.parts:
        if part in section_folders:
            return part
    return None


class ObsidianToJekyllConverter:
    """Syncs an Obsidian vault and Jekyll scaffold into a Jekyll-ready source tree,
    using a content-hash manifest (via SiteSync) to skip unchanged files on repeat runs."""

    IGNORED_VAULT_ITEMS = ['.obsidian', 'website-whiteboard.excalidraw']
    INCLUDED_JEKYLL_ITEMS = ['CNAME',
                             '_config.yaml',
                             'index.md',
                             'assets',
                             'posts',
                             '_includes',
                             '_layouts',
                             '_data',
                             'vision']
    IGNORED_FRONTMATTER_FILES = ['index.md', 'home.md', 'vision.md']
    SECTION_FOLDERS = ['vision']
    IMAGE_ASSET_GLOBS = ('*.png', '*.svg')

    def __init__(self, obsidian_vault_location: Path, output_location: Path, source_location: Path):
        self.obsidian_vault_location = obsidian_vault_location
        self.output_location = output_location
        self.source_location = source_location
        self.site_sync = SiteSync(output_location / MANIFEST_FILENAME)

    def begin_run(self) -> None:
        """Reset per-run sync tracking state (loads the on-disk manifest).
        Called at the start of run(), and reusable directly in tests to
        simulate a second, separate invocation of the converter."""
        self.site_sync.begin_run()

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
        self.site_sync.prune_stale_files()
        self.site_sync.save()

    def copy_vault_images_into_assets_directory(self) -> None:
        output_image_path = self.output_location / 'assets/images/'
        output_image_path.mkdir(parents=True, exist_ok=True)
        for glob_pattern in self.IMAGE_ASSET_GLOBS:
            for image_file in self.obsidian_vault_location.rglob(glob_pattern):
                self.site_sync.sync_file(image_file, output_image_path / image_file.name)

    def parse_markdown_files_for_jekyll(self, note_path_lookup: dict[str, str]) -> None:
        for dest_path in self.site_sync.changed_dest_paths:
            if dest_path.suffix != '.md':
                continue

            if is_excalidraw_note(dest_path):
                # Must happen before frontmatter injection below — this
                # overwrites the whole file, so frontmatter would be lost
                # if it were added first.
                swap_excalidraw_note_with_image_embed(dest_path)

            if dest_path.name in self.IGNORED_FRONTMATTER_FILES:
                print(f"Skipping adding of frontmatter to '{dest_path.name}'")
            elif dest_path.name in ['about.md']:
                add_frontmatter_to_file(dest_path,
                                        include_permalink=True)
            elif find_section(dest_path, self.SECTION_FOLDERS):
                section_root = find_section(dest_path, self.SECTION_FOLDERS)
                add_frontmatter_to_file(dest_path,
                                        file_layout='section',
                                        section=section_root.capitalize(),
                                        include_permalink=True)
            else:
                add_frontmatter_to_file(dest_path)

            process_markdown_for_jekyll(dest_path, note_path_lookup)

    def copy_jekyll_resources(self) -> None:
        for source_item in self.source_location.iterdir():
            if source_item.name not in self.INCLUDED_JEKYLL_ITEMS:
                continue
            dest_path = self.output_location / source_item.name
            if source_item.is_dir():
                self.site_sync.sync_tree(source_item, dest_path)
            else:
                self.site_sync.sync_file(source_item, dest_path)

    def copy_vault_resources(self) -> None:
        for vault_item in self.obsidian_vault_location.iterdir():
            if vault_item.name in self.IGNORED_VAULT_ITEMS:
                continue
            if vault_item.name == 'posts':
                image_suffixes = {'.png', '.jpg', '.jpeg', '.gif', '.svg'}
                # Jekyll requires _posts filenames to be YYYY-MM-DD-title.md
                # (lowercase, hyphens only) — Obsidian note titles are free-form,
                # so slugify on the way out.
                self.site_sync.sync_tree(vault_item,
                                         self.output_location / '_posts',
                                         exclude_suffixes=image_suffixes,
                                         dest_filename=slugify_filename)
            else:
                self.site_sync.sync_tree(vault_item, self.output_location / vault_item.name)


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
