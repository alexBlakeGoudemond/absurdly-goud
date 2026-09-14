#!/usr/bin/env python3
"""
Escapes bare pipe (`|`) characters inside Markdown link syntax so kramdown
doesn't misinterpret them as GFM/table column separators.

Kramdown (particularly kramdown-parser-gfm, which GitHub Pages/Jekyll use
for table support) treats an unescaped `|` as a potential table-column
separator, even when it appears inside a Markdown link's text or URL, e.g.
`[Wikilink | with pipe](https://example.com)`. Outside of an actual table,
this confuses kramdown's parser and the link -- and everything after the
pipe on that line -- can silently fail to render.

Escaping the pipe as `\\|` makes kramdown treat it as a literal character
everywhere, table or not, per kramdown's own escaping rules.
"""

import re

from scripts.parsing_markdown.markdown_regions import (
    apply_outside_code_blocks_and_code_spans,
    iter_fenced_lines,
)

# A Markdown link or image: [text](url). Deliberately matches just this
# `[...](...)` shape -- by the time this runs, Obsidian's own `![[img]]` and
# `[[Note]]` syntaxes have already been converted to it (or to Jekyll
# includes), so this single pattern covers everything left: plain links,
# and the `[Alt Text]({% link ... %}...)` output of wikilink conversion.
MARKDOWN_LINK_PATTERN = re.compile(r'\[([^\]]*)\]\(([^)]+)\)')

# A `|` not already preceded by a backslash, so a pipe someone already
# escaped by hand (`\|`) is left alone instead of becoming `\\|`.
UNESCAPED_PIPE_PATTERN = re.compile(r'(?<!\\)\|')

TABLE_DELIMITER_PATTERN = re.compile(
    r'^\s*\|?(?:\s*:?-+:?\s*\|)+\s*:?-+:?\s*\|?\s*$|^\s*\|\s*:?-+:?\s*\|\s*$'
)


def is_table_delimiter(line: str) -> bool:
    stripped = line.strip()
    if stripped.startswith('>'):
        return False
    return bool(TABLE_DELIMITER_PATTERN.match(line))


def is_table_row(line: str) -> bool:
    stripped = line.strip()
    if not stripped or stripped.startswith('>'):
        return False
    return bool(UNESCAPED_PIPE_PATTERN.search(line))


def pad_markdown_tables_in_lines(lines: list[str]) -> list[str]:
    table_ranges: list[tuple[int, int]] = []
    i = 0
    n = len(lines)
    while i < n:
        if (
            is_table_delimiter(lines[i])
            and i > 0
            and is_table_row(lines[i - 1])
            and not is_table_delimiter(lines[i - 1])
        ):
            start = i - 1
            j = i + 1
            while j < n and is_table_row(lines[j]) and not is_table_delimiter(lines[j]):
                j += 1
            end = j - 1
            table_ranges.append((start, end))
            i = j
        else:
            i += 1

    if not table_ranges:
        return lines

    output: list[str] = []
    current_line = 0
    for start, end in table_ranges:
        while current_line < start:
            output.append(lines[current_line])
            current_line += 1

        if not output:
            output.extend(['', ''])
        elif output[-1] != '':
            output.append('')

        while current_line <= end:
            output.append(lines[current_line])
            current_line += 1

        if current_line == n:
            output.extend(['', ''])
        else:
            output.append('')

    while current_line < n:
        if lines[current_line] == '' and output and output[-1] == '':
            current_line += 1
            continue
        output.append(lines[current_line])
        current_line += 1

    return output


def pad_markdown_tables_outside_code_blocks(content: str) -> str:
    output_lines: list[str] = []
    non_fenced_buffer: list[str] = []

    def flush_non_fenced_buffer() -> None:
        if non_fenced_buffer:
            padded = pad_markdown_tables_in_lines(non_fenced_buffer)
            output_lines.extend(padded)
            non_fenced_buffer.clear()

    for fenced_line in iter_fenced_lines(content):
        if fenced_line.in_fence or fenced_line.is_fence_boundary:
            flush_non_fenced_buffer()
            output_lines.append(fenced_line.line)
        else:
            non_fenced_buffer.append(fenced_line.line)

    flush_non_fenced_buffer()
    return '\n'.join(output_lines)


def escape_pipes(text: str) -> str:
    return UNESCAPED_PIPE_PATTERN.sub(r'\\|', text)


def escape_pipes_in_markdown_links(segment: str) -> str:
    def replace(match: re.Match) -> str:
        link_text, url = match.group(1), match.group(2)
        return f'[{escape_pipes(link_text)}]({escape_pipes(url)})'

    return MARKDOWN_LINK_PATTERN.sub(replace, segment)


def escape_pipes_in_links_outside_code_blocks_and_code_spans(content: str) -> str:
    """
    Escapes bare `|` characters found inside Markdown link text or URLs,
    everywhere EXCEPT inside fenced ```code blocks and inline `code` spans,
    so a documentation example isn't rewritten.

    Must run AFTER wikilink conversion (convert_wikilink_note_links_...) --
    that step relies on an *unescaped* `|` as the delimiter between
    `[[Note` and `Alt Text]]`, so escaping pipes first would break it.
    Running after is safe: by then any real wikilink pipe has already been
    consumed, and any pipe still present is either stray content or
    unrelated to wikilink syntax.
    """
    escaped = apply_outside_code_blocks_and_code_spans(content, escape_pipes_in_markdown_links)
    return pad_markdown_tables_outside_code_blocks(escaped)
