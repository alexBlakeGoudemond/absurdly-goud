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

# One or more consecutive blank lines, i.e. the gap between two blocks.
# The `+` matters for correctly identifying block boundaries when hunting
# for headings below — a gap of several blank lines is still just one gap
# between two blocks, not several empty blocks in between.
_BLOCK_BREAK_PATTERN = re.compile(r'\n(?:[ \t]*\n)+')

# A block that is a heading and nothing else: a single line starting with
# 1-6 '#' characters. Headings are skipped when hunting for the "first
# paragraph" — the excerpt should start after the first real prose block,
# not get wedged directly under a title.
_HEADING_ONLY_PATTERN = re.compile(r'\A#{1,6}[ \t]+\S.*\Z')


def _is_heading_only_block(block: str) -> bool:
    stripped = block.strip('\n')
    return '\n' not in stripped and bool(_HEADING_ONLY_PATTERN.match(stripped))


def insert_excerpt_marker_after_first_paragraph(content: str) -> str:
    """
    Finds the first non-heading paragraph in `content` — skipping a leading
    YAML frontmatter block, if present, and skipping over any heading blocks
    (`# ...` through `###### ...`) that precede it — and inserts
    EXCERPT_MARKER on its own line directly after that paragraph.

    If the marker is already present, or there's no paragraph after the
    leading headings to separate the marker from, `content` is returned
    unchanged.
    """
    if EXCERPT_MARKER in content:
        return content

    frontmatter_match = _FRONTMATTER_PATTERN.match(content)
    frontmatter = frontmatter_match.group(0) if frontmatter_match else ''
    body = content[len(frontmatter):]

    body_without_leading_blank_lines = body.lstrip('\n')
    leading_blank_lines_length = len(body) - len(body_without_leading_blank_lines)

    breaks = list(_BLOCK_BREAK_PATTERN.finditer(body_without_leading_blank_lines))
    if not breaks:
        # Only one block total — nothing to separate it from.
        return content

    block_starts = [0] + [b.end() for b in breaks]
    block_ends = [b.start() for b in breaks] + [len(body_without_leading_blank_lines)]

    # Walk blocks in order, skipping leading headings, looking for the first
    # non-heading block that still has a block *after* it (excluding the
    # final block — there must be something to separate it from).
    insertion_break_index = None
    for index in range(len(breaks)):
        block = body_without_leading_blank_lines[block_starts[index]:block_ends[index]]
        if _is_heading_only_block(block):
            continue
        insertion_break_index = index
        break

    if insertion_break_index is None:
        return content

    insert_at = leading_blank_lines_length + breaks[insertion_break_index].start()
    return f'{frontmatter}{body[:insert_at]}\n\n{EXCERPT_MARKER}{body[insert_at:]}'


def add_excerpt_marker_to_file(markdown_file: Path) -> None:
    """Reads `markdown_file`, inserts the excerpt marker if needed, and
    writes it back only if the content actually changed."""
    content = markdown_file.read_text(encoding="utf-8")
    new_content = insert_excerpt_marker_after_first_paragraph(content)
    if new_content != content:
        markdown_file.write_text(new_content, encoding="utf-8")