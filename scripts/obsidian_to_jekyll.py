#!/usr/bin/env python3

import argparse
from pathlib import Path
import shutil
import re


def main():
    argument_parser = argparse.ArgumentParser(
        description='Export Obsidian vault to a Jekyll-friendly source tree and write into repo or output dir')
    argument_parser.add_argument('--vault', default='absurdly-goud-obsidian')
    argument_parser.add_argument('--src-root', default='.')
    argument_parser.add_argument('--out-dir', default='site_src',
                                 help='If provided, generate the site source into this directory and do NOT sync into the repo')
    arguments = argument_parser.parse_args()

    obsidian_vault_location, output_location, source_location = extract_command_line_arguments(arguments)

    if not obsidian_vault_location.exists():
        print(f"Vault path '{obsidian_vault_location}' does not exist. Nothing to do.")
        return

    if output_location.exists():
        shutil.rmtree(output_location)

    copy_vault_resources(obsidian_vault_location, output_location)
    copy_jekyll_resources(source_location, output_location)

    # recursive glob (rglob) will find all markdown files for us
    for markdown_file in output_location.rglob('*.md'):
        add_frontmatter_to_file(markdown_file)


def add_frontmatter_to_file(markdown_file, file_layout='default'):
    file_title = extract_title_from_file_name(markdown_file.name)
    file_path = Path(markdown_file)
    file_content = file_path.read_text(encoding="utf-8")

    frontmatter = f"""---
layout: {file_layout}
title: {file_title}
---

"""
    file_path.write_text(frontmatter + file_content, encoding="utf-8")

def extract_title_from_file_name(file_name: str) -> str:
    filename_with_leading_timestamp = re.compile(r'^\d{4}-\d{2}-\d{2}-')
    filename_ending_in_md = re.compile(r'.md')
    file_title = filename_with_leading_timestamp.sub('', file_name)
    file_title = filename_ending_in_md.sub('', file_title)
    return file_title


def copy_jekyll_resources(source_location: Path, output_location: Path):
    included_items = ['assets', 'CNAME', 'posts', '_includes', 'layouts', '_config.yaml', 'index.md']
    for source_item in source_location.iterdir():
        source_item_name = source_item.name
        if source_item_name not in included_items:
            continue
        print(f"Copying '{source_item_name}' to '{output_location}/{source_item_name}'")
        if source_item.is_dir():
            shutil.copytree(source_item, output_location / source_item_name)
        else:
            shutil.copy2(source_item, output_location / source_item_name)


def copy_vault_resources(obsidian_vault_location: Path, output_location: Path):
    ignored_items = ['.obsidian']
    print(f"ignored_items: '{ignored_items}'")
    for vault_item in obsidian_vault_location.iterdir():
        vault_item_name = vault_item.name
        if vault_item_name in ignored_items:
            continue
        match vault_item_name:
            case 'posts':
                print(f"Copying '{vault_item_name}' to '{output_location}/_posts'")
                shutil.copytree(vault_item, output_location / '_posts')
            case _:
                print(f"Copying '{vault_item_name}' to '{output_location}/{vault_item_name}'")
                shutil.copytree(vault_item, output_location / vault_item_name)


def extract_command_line_arguments(args: argparse.Namespace) -> tuple[Path, Path, Path]:
    obsidian_vault_location = Path(args.vault)
    output_location = Path(args.out_dir)
    if args.src_root == Path("."):
        source_location = Path(__file__).resolve().parents[1]
    else:
        source_location = Path(args.src_root)
    return obsidian_vault_location, output_location, source_location


if __name__ == '__main__':
    main()
