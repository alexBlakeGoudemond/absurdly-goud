"""
Inserts Jekyll's `<!--more-->` excerpt separator directly after a markdown
file's first paragraph, so Jekyll's automatic excerpt (used on listing/index
pages) ends at a sensible boundary instead of falling back to the whole post.
"""

import re
from pathlib import Path

EXCERPT_MARKER = "<!--more-->"

# A leading YAML frontmatter block: '---\n' ... '\n---\n'. Matched greedily
# from the very start of the file only — a mid-file '---' (e.g. a markdown
# horizontal rule) must never be mistaken for a frontmatter delimiter.
_FRONTMATTER_PATTERN = re.compile(r'\A---\n.*?\n---\n', re.DOTALL)

# The first blank line (allowing trailing whitespace on it) marks the end
# of the first paragraph.
_PARAGRAPH_BREAK_PATTERN = re.compile(r'\n[ \t]*\n')


def insert_excerpt_marker_after_first_paragraph(content: str) -> str:
    """
    Finds the first paragraph in `content` — skipping a leading YAML
    frontmatter block, if present — and inserts EXCERPT_MARKER on its own
    line directly after it.

    A "paragraph" here is the first run of non-blank lines, ending at the
    first blank line. If the marker is already present, or the content has
    no second paragraph to separate the first one from, `content` is
    returned unchanged.
    """
    if EXCERPT_MARKER in content:
        return content

    frontmatter_match = _FRONTMATTER_PATTERN.match(content)
    frontmatter = frontmatter_match.group(0) if frontmatter_match else ''
    body = content[len(frontmatter):]

    body_without_leading_blank_lines = body.lstrip('\n')
    leading_blank_lines_length = len(body) - len(body_without_leading_blank_lines)

    break_match = _PARAGRAPH_BREAK_PATTERN.search(body_without_leading_blank_lines)
    if break_match is None:
        # Only one paragraph (or no body at all) — nothing to separate.
        return content

    insert_at = leading_blank_lines_length + break_match.start()
    return f'{frontmatter}{body[:insert_at]}\n\n{EXCERPT_MARKER}{body[insert_at:]}'


def add_excerpt_marker_to_file(markdown_file: Path) -> None:
    """Reads `markdown_file`, inserts the excerpt marker if needed, and
    writes it back only if the content actually changed."""
    content = markdown_file.read_text(encoding="utf-8")
    new_content = insert_excerpt_marker_after_first_paragraph(content)
    if new_content != content:
        markdown_file.write_text(new_content, encoding="utf-8")