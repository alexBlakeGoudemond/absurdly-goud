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


def process_image_notation_in_markdown_file(markdown_file: Path) -> None:
    """Convert Obsidian-style image notation ![Alt text](image.png) to Jekyll include notation."""
    content = markdown_file.read_text(encoding="utf-8")
    markdown_image_pattern = r'!\[(.+)\]\((.+)\)'
    all_matches = re.findall(markdown_image_pattern, content)
    for match in all_matches:
        image_alt_text = match[0]
        image_name = match[1]
        jekyll_image_includes_notation = (
            convert_markdown_image_notation_to_jekyll_includes_image_notation(image_name, image_alt_text))
        content = content.replace(f"![{image_alt_text}]({image_name})", jekyll_image_includes_notation)
    markdown_file.write_text(content, encoding="utf-8")


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

    IGNORED_VAULT_ITEMS = ['.obsidian']
    INCLUDED_JEKYLL_ITEMS = ['assets', 'CNAME', 'posts', '_includes', '_layouts', '_config.yaml', 'index.md', '_data']
    IGNORED_FRONTMATTER_FILES = ['index.md', 'home.md']

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
        self.collect_images_in_assets_directory()

        self.add_frontmatter_to_markdown_files()
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

    def sync_tree(self, source_dir: Path, dest_dir: Path) -> None:
        """Walk source_dir recursively, syncing each file individually."""
        for source_path in source_dir.rglob("*"):
            if source_path.is_dir():
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

    def collect_images_in_assets_directory(self) -> None:
        output_image_path = self.output_location / 'assets/images/'
        output_image_path.mkdir(parents=True, exist_ok=True)
        for image_file in self.obsidian_vault_location.rglob('*.png'):
            # jekyll_image_includes_notation = convert_markdown_image_notation_to_jekyll_includes_image_notation(
            # print(f"jekyll_image_includes_notation: {jekyll_image_includes_notation}")
            # convert_markdown_image_notation_to_jekyll_includes_notation()
            self.sync_file(image_file, output_image_path / image_file.name)

    def add_frontmatter_to_markdown_files(self) -> None:
        """Only inject frontmatter into files actually (re)written this run —
        prevents double-prepending frontmatter onto cache-hit files."""
        for dest_path in self.changed_dest_paths:
            if dest_path.suffix != '.md':
                continue
            if dest_path.name in self.IGNORED_FRONTMATTER_FILES:
                continue
            if dest_path.name == 'about.md':
                self.add_frontmatter_to_file(dest_path, include_permalink=True)
            else:
                self.add_frontmatter_to_file(dest_path)

    @staticmethod
    def add_frontmatter_to_file(markdown_file: Path, file_layout='default', include_permalink=False) -> None:
        file_title = ObsidianToJekyllConverter.extract_title_from_file_name(markdown_file.name)
        file_content = markdown_file.read_text(encoding="utf-8")
        file_permalink = f"/{file_title}/" if include_permalink else ""

        frontmatter = dedent(f"""
            ---
            layout: {file_layout}
            title: {file_title}
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
            dest_name = '_posts' if vault_item.name == 'posts' else vault_item.name
            self.sync_tree(vault_item, self.output_location / dest_name)


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
