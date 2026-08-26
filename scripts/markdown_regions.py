#!/usr/bin/env python3
"""
Shared helpers for telling prose apart from fenced code blocks (``` / ~~~) and
inline `code` spans in Markdown content.

Any module that must skip a conversion inside code — wikilinks, images,
codeblock escaping — builds on these primitives instead of re-implementing
its own fence-tracking loop.
"""

import re
from typing import Callable, Iterator, NamedTuple

MARKDOWN_FENCE_PATTERN = re.compile(r'^(\s*)(```|~~~)(\S*)\s*$')
MARKDOWN_INLINE_CODE_PATTERN = re.compile(r'`[^`]*`')


class FencedLine(NamedTuple):
    """One line of content, classified by its position relative to a fenced
    code block.

    `is_fence_boundary` is True for the opening or closing fence delimiter
    line itself (the ``` or ~~~ line). It's still "content" that callers pass
    through, but it's also the point where a caller like codeblock_escaping
    needs to insert something (e.g. a {% raw %} tag).
    """
    line: str
    in_fence: bool
    is_fence_boundary: bool
    fence_opened: bool  # True only on the line that just opened a fence
    fence_closed: bool  # True only on the line that just closed a fence


def iter_fenced_lines(content: str) -> Iterator[FencedLine]:
    """Walks `content` line by line, tracking whether each line sits inside a
    fenced ``` or ~~~ code block.

    A fence only closes on a delimiter using the SAME marker that opened it
    (mirroring Markdown/kramdown behaviour), so e.g. a ~~~ line inside an
    already-open ``` fence is just fenced content, not a close.
    """
    in_fence = False
    fence_marker = None

    for line in content.split('\n'):
        fence_match = MARKDOWN_FENCE_PATTERN.match(line)
        if fence_match:
            marker = fence_match.group(2)
            if not in_fence:
                in_fence = True
                fence_marker = marker
                yield FencedLine(line, in_fence=True, is_fence_boundary=True,
                                 fence_opened=True, fence_closed=False)
            elif marker == fence_marker:
                in_fence = False
                yield FencedLine(line, in_fence=False, is_fence_boundary=True,
                                 fence_opened=False, fence_closed=True)
            else:
                # A fence-looking line with a different marker while already
                # inside a fence (e.g. ~~~ inside a ``` block) is just content.
                yield FencedLine(line, in_fence=True, is_fence_boundary=False,
                                 fence_opened=False, fence_closed=False)
            continue

        yield FencedLine(line, in_fence=in_fence, is_fence_boundary=False,
                         fence_opened=False, fence_closed=False)


def apply_outside_fenced_blocks(content: str, transform: Callable[[str], str]) -> str:
    """Applies `transform` to each line of `content` that sits outside a
    fenced code block, leaving fence delimiter lines and fenced content
    untouched."""
    output_lines = []
    for fenced_line in iter_fenced_lines(content):
        if fenced_line.in_fence or fenced_line.is_fence_boundary:
            output_lines.append(fenced_line.line)
        else:
            output_lines.append(transform(fenced_line.line))
    return '\n'.join(output_lines)


def apply_outside_inline_code(line: str, transform: Callable[[str], str]) -> str:
    """Applies `transform` to the parts of a single `line` that sit outside
    `inline code` spans, leaving inline code spans untouched."""
    segments = []
    last_end = 0
    for code_match in MARKDOWN_INLINE_CODE_PATTERN.finditer(line):
        segments.append(transform(line[last_end:code_match.start()]))
        segments.append(code_match.group(0))  # leave inline code untouched
        last_end = code_match.end()
    segments.append(transform(line[last_end:]))
    return ''.join(segments)
