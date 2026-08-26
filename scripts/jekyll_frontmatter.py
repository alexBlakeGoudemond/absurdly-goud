#!/usr/bin/env python3
"""
Builds and injects Jekyll YAML frontmatter into a converted markdown file:
deriving a display title and (optionally) a permalink from the filename and
its location, then prepending the frontmatter block — replacing any
pre-existing one.
"""

import re
from pathlib import Path

EXISTING_FRONTMATTER_PATTERN = re.compile(r'\A---\n.*?\n---\n', re.DOTALL)


def extract_title_from_file_name(file_name: str) -> str:
    """Only retain the important parts of the filename"""
    filename_with_leading_timestamp = re.compile(r'^\d{4}-\d{2}-\d{2}-')
    filename_ending_in_md = re.compile(r'\.md$')
    filename_excalidraw_infix = re.compile(r'\.excalidraw$')

    file_title = filename_with_leading_timestamp.sub('', file_name)
    file_title = filename_ending_in_md.sub('', file_title)
    file_title = filename_excalidraw_infix.sub('', file_title)
    return file_title


def display_title_from_slug(file_title: str) -> str:
    """Turns a hyphenated slug into a readable page title, e.g.
    'website-inspiration' -> 'Inspiration', 'my-cool-note' -> 'My Cool Note'."""
    return file_title.replace('-', ' ').title()


def build_permalink(markdown_file: Path, file_title: str, section: str | None) -> str:
    if section is None:
        return f"/{file_title.lower()}/"

    subfolder = markdown_file.parent.name.lower()
    slug = file_title.lower()

    # If the cleaned filename matches its own folder (e.g. website-design.md
    # in design/), treat it as that folder's index page rather than stuttering
    # the URL (/vision/design/ instead of /vision/design/design/).
    if slug == subfolder:
        return f"/{section.lower()}/{subfolder}/"
    return f"/{section.lower()}/{subfolder}/{slug}/"


def build_frontmatter(file_layout: str, title: str, permalink: str = "", section: str | None = None) -> str:
    lines = ["---", f"layout: {file_layout}", f'title: "{title}"']
    if section:
        lines.append(f"section: {section}")
    if permalink:
        lines.append(f"permalink: {permalink}")
    lines.append("---")
    lines.append("")
    lines.append("")
    return "\n".join(lines)


def strip_existing_frontmatter(content: str) -> str:
    """Obsidian plugins (e.g. Excalidraw) often prepend their own YAML
    frontmatter block. Jekyll tolerates only one frontmatter block per file,
    so strip any pre-existing block before prepending ours — otherwise
    kramdown hits a second '---' fence and the raw YAML leaks into the
    rendered page body."""
    return EXISTING_FRONTMATTER_PATTERN.sub('', content, count=1)


def add_frontmatter_to_file(markdown_file: Path,
                            file_layout='default',
                            include_permalink=False,
                            section: str | None = None) -> None:
    file_title = extract_title_from_file_name(markdown_file.name)
    file_content = strip_existing_frontmatter(markdown_file.read_text(encoding="utf-8"))

    file_permalink = ""
    if include_permalink:
        file_permalink = build_permalink(markdown_file, file_title, section)

    frontmatter = build_frontmatter(file_layout, display_title_from_slug(file_title), file_permalink, section)
    markdown_file.write_text(frontmatter + file_content, encoding="utf-8")
