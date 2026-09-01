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
from typing import Any

from scripts.parsing_markdown.codeblock_escaping import escape_markdown_code_blocks_for_jekyll
from scripts.parsing_markdown.excalidraw_embeds import is_excalidraw_note, swap_excalidraw_note_with_image_embed
from scripts.parsing_markdown.markdown_excerpt import add_excerpt_marker_to_file
from scripts.parsing_markdown.filenames import slugify_filename
from scripts.parsing_markdown.jekyll_frontmatter import add_frontmatter_to_file
from scripts.parsing_markdown.markdown_images import (
    build_image_path_lookup,
    convert_markdown_image_embeds_outside_code_blocks_and_code_spans,
    convert_wikilink_image_embeds_outside_code_blocks_and_code_spans
)
from scripts.parsing_markdown.pipe_escaping import escape_pipes_in_links_outside_code_blocks_and_code_spans
from scripts.parsing_markdown.site_sync import SiteSync
from scripts.parsing_markdown.wikilinks import build_note_path_lookup, convert_wikilink_note_links_outside_code_blocks_and_code_spans

MANIFEST_FILENAME = ".manifest.json"


def process_markdown_for_jekyll(
        markdown_file: Path, note_path_lookup: dict[str, str],
        image_path_lookup: dict[str, str]
) -> None:
    """Convert Obsidian-style notations to formats that Jekyll recognizes"""
    print(f"processing markdown for '{markdown_file.name}'")
    content = markdown_file.read_text(encoding="utf-8")
    # Obsidian's own `![[image.png]]` embed syntax is normalized to standard
    # `![alt](src)` markdown FIRST, before wikilinks run — otherwise a `[[...]]`
    # preceded by `!` gets mistaken for a note link by the wikilink pattern
    # and fails lookup (it's an image filename, not a note).
    new_content = convert_wikilink_image_embeds_outside_code_blocks_and_code_spans(content)
    new_content = convert_wikilink_note_links_outside_code_blocks_and_code_spans(new_content, note_path_lookup)
    new_content = convert_markdown_image_embeds_outside_code_blocks_and_code_spans(new_content, image_path_lookup)
    new_content = escape_markdown_code_blocks_for_jekyll(new_content)
    new_content = escape_pipes_in_links_outside_code_blocks_and_code_spans(new_content)
    if new_content != content:
        markdown_file.write_text(new_content, encoding="utf-8")


def find_parent_section(dest_path: Path, section_folders: list[str]) -> str | None:
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
    IMAGE_ASSET_GLOBS = ('*.png', '*.svg', '*.gif')
    IMAGE_SUFFIXES = {'.png', '.jpg', '.jpeg', '.gif', '.svg', '*.gif'}

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
        # be a valid wikilink target for a changed one. Same reasoning
        # applies to image_path_lookup: it must reflect the final bucketed
        # assets/ tree, not just the images copied this run.
        note_path_lookup = build_note_path_lookup(self.site_sync.new_manifest, self.output_location)
        image_path_lookup = build_image_path_lookup(self.output_location / 'assets')

        self.parse_markdown_files_for_jekyll(note_path_lookup, image_path_lookup)
        self.site_sync.prune_stale_files()
        self.site_sync.save()

    def copy_vault_images_into_assets_directory(self) -> None:
        assets_root = self.output_location / 'assets'
        for glob_pattern in self.IMAGE_ASSET_GLOBS:
            for image_file in self.obsidian_vault_location.rglob(glob_pattern):
                relative_path = image_file.relative_to(self.obsidian_vault_location)
                # Bucket by the vault's top-level parent directory (e.g. '88x31',
                # 'posts') rather than preserving the full nested path — images
                # land flat inside that bucket.
                if len(relative_path.parts) > 1:
                    top_level_dir = relative_path.parts[0]
                    dest_dir = assets_root / top_level_dir
                else:
                    # Image sits directly at the vault root, with no parent dir.
                    dest_dir = assets_root
                dest_dir.mkdir(parents=True, exist_ok=True)
                self.site_sync.sync_file(image_file, dest_dir / image_file.name)

    def parse_markdown_files_for_jekyll(
            self, note_path_lookup: dict[str, str],
            image_path_lookup: dict[str, str]
    ) -> None:
        last_published_by_dest = self.filename_to_last_published()

        for dest_path in self.site_sync.changed_dest_paths:
            if dest_path.suffix != '.md':
                continue

            if is_excalidraw_note(dest_path):
                # Must happen before frontmatter injection below — this
                # overwrites the whole file, so frontmatter would be lost
                # if it were added first.
                swap_excalidraw_note_with_image_embed(dest_path)

            self.add_frontmatter_if_needed(dest_path, last_published_by_dest[dest_path])
            self.add_excerpt_if_needed(dest_path)

            process_markdown_for_jekyll(dest_path, note_path_lookup, image_path_lookup)

    def filename_to_last_published(self) -> dict[Path, Any]:
        last_published_by_dest = {
            Path(entry["dest"]): entry["last_published"]
            for entry in self.site_sync.new_manifest.values()
        }
        return last_published_by_dest

    def add_frontmatter_if_needed(self, dest_path: Path, last_published: str):
        if dest_path.name in self.IGNORED_FRONTMATTER_FILES:
            print(f"Skipping adding of frontmatter to '{dest_path.name}'")
        elif '_posts' in dest_path.parts:
            add_frontmatter_to_file(dest_path,
                                    file_layout='post',
                                    include_permalink=True,
                                    last_published=last_published)
        elif dest_path.name in ['about.md']:
            add_frontmatter_to_file(dest_path,
                                    include_permalink=True,
                                    last_published=last_published)
        elif find_parent_section(dest_path, self.SECTION_FOLDERS):
            section_root = find_parent_section(dest_path, self.SECTION_FOLDERS)
            add_frontmatter_to_file(dest_path,
                                    file_layout='section',
                                    section=section_root.capitalize(),
                                    include_permalink=True,
                                    last_published=last_published)
        else:
            add_frontmatter_to_file(dest_path, last_published=last_published)

    def add_excerpt_if_needed(self, dest_path: Path) -> None:
        """Inserts Jekyll's `<!--more-->` marker after the file's first
        paragraph. Runs after frontmatter injection so the frontmatter-skip
        logic in add_excerpt_marker_to_file has a real frontmatter block to
        skip; is a no-op (idempotent) if the marker is already present or
        the file has no second paragraph to separate from."""
        add_excerpt_marker_to_file(dest_path)

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
        """Images are excluded from every folder copied here — not just
        posts/ — because copy_vault_images_into_assets_directory is the
        single place responsible for landing images in the output tree
        (bucketed under assets/). Without this exclusion, an image sitting
        in any other vault folder (e.g. 88x31/) would get copied BOTH here,
        as part of its folder, AND into assets/, duplicating it in the
        output."""
        for vault_item in self.obsidian_vault_location.iterdir():
            if vault_item.name in self.IGNORED_VAULT_ITEMS:
                continue
            if vault_item.name == 'posts':
                # Jekyll requires _posts filenames to be YYYY-MM-DD-title.md
                # (lowercase, hyphens only) — Obsidian note titles are free-form,
                # so slugify on the way out.
                self.site_sync.sync_tree(vault_item,
                                         self.output_location / '_posts',
                                         exclude_suffixes=self.IMAGE_SUFFIXES,
                                         dest_filename=slugify_filename)
            else:
                self.site_sync.sync_tree(vault_item,
                                         self.output_location / vault_item.name,
                                         exclude_suffixes=self.IMAGE_SUFFIXES)


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