#!/usr/bin/env python3
"""
Converts Obsidian-style callouts (`> [!type] Title` blockquotes) into Jekyll
`{% capture %}` + `{% include callout.html %}` tags, so the site can render
them with custom styling instead of as a plain, unstyled blockquote.

This module only produces the Liquid syntax that calls the callout include —
it does not create or depend on `_includes/callout.html` itself. Jekyll only
resolves an `{% include %}` at site-build time, not at Liquid-parse time, so
these tests can (and should) pass before that include file exists.

Must run AFTER wikilinks.py and markdown_images.py in the pipeline. By that
point a callout's body no longer contains raw Obsidian syntax — a wikilink
is already `[text]({% link ... %})` and an image embed is already
`{% include image.html ... %}` — so this module does no Obsidian-syntax
resolution of its own. It only extracts whatever markdown/Liquid is already
inside the blockquote and re-wraps it, unchanged, inside a `{% capture %}`.
"""

import itertools
import re
from typing import Iterator, NamedTuple, Optional

from scripts.parsing_markdown.markdown_regions import iter_fenced_lines

# First line of a callout blockquote: `> [!type]`, `>[!type]+`, `> [!type]- Title`
# The fold marker is preserved here as part of the parsed callout state:
# `+` means start expanded, `-` means start collapsed. The type-identifier
# character class is deliberately permissive (any custom word is accepted
# here) — TYPE_ALIASES below is what decides whether it's one of Obsidian's
# 13 known types or an unrecognized/custom one.
CALLOUT_HEADER_PATTERN = re.compile(
    r'^>[ \t]?\[!(?P<type>[A-Za-z][\w-]*)\](?P<fold>[+-]?)[ \t]*(?P<title>.*)$'
)

# Any blockquote continuation line, callout or not: `>`, `> text`, `>text`.
# A callout block is a run of consecutive lines all matching this — a truly
# blank line (no `>` at all) ends the blockquote, same as standard Markdown.
BLOCKQUOTE_LINE_PATTERN = re.compile(r'^>[ \t]?(?P<rest>.*)$')

# Obsidian's 13 built-in callout types, keyed by canonical type, with the
# case-insensitive aliases that all resolve to the same visual style.
# https://help.obsidian.md/Editing+and+formatting/Callouts
_CANONICAL_TYPES_WITH_ALIASES: dict[str, list[str]] = {
    "note": [],
    "abstract": ["summary", "tldr"],
    "info": [],
    "todo": [],
    "important": ["tip", "hint"],
    "success": ["check", "done"],
    "question": ["help", "faq"],
    "warning": ["caution", "attention"],
    "failure": ["fail", "missing"],
    "danger": ["error"],
    "bug": [],
    "example": [],
    "quote": ["cite"],
}

TYPE_ALIASES: dict[str, str] = {}
for _canonical, _aliases in _CANONICAL_TYPES_WITH_ALIASES.items():
    TYPE_ALIASES[_canonical] = _canonical
    for _alias in _aliases:
        TYPE_ALIASES[_alias] = _canonical

DEFAULT_TITLES: dict[str, str] = {
    canonical: canonical.capitalize() for canonical in _CANONICAL_TYPES_WITH_ALIASES
}

# Obsidian itself renders an unrecognized `[!type]` using "note" styling
# while still showing the typed word as the title (unless a custom title was
# given). Mirrored here for the same reason: a mistyped or intentionally
# custom type still gets a styled callout instead of silently falling
# through to a plain, unstyled blockquote.
FALLBACK_CANONICAL_TYPE = "note"


class CalloutBlock(NamedTuple):
    canonical_type: str
    title: str
    collapsible: bool = False
    content: str = ''
    initially_collapsed: bool = False


def _resolve_canonical_type_and_title(raw_type: str, custom_title: str) -> tuple[str, str]:
    canonical_type = TYPE_ALIASES.get(raw_type.lower())
    custom_title = custom_title.strip()

    if canonical_type is None:
        # Unknown/custom type: fall back to "note" styling but keep the
        # author's original word as the visible title, mirroring Obsidian.
        return FALLBACK_CANONICAL_TYPE, custom_title or raw_type

    return canonical_type, custom_title or DEFAULT_TITLES[canonical_type]


def _liquid_quote(value: str) -> str:
    """Wraps `value` in whichever quote character it doesn't itself contain
    — Liquid string literals have no escape sequence for a quote character
    matching their own delimiter. In the rare case a title contains both
    quote characters, double quotes are used with the conflicting
    characters stripped, rather than producing invalid Liquid."""
    if '"' not in value:
        return f'"{value}"'
    if "'" not in value:
        return f"'{value}'"
    sanitized = value.replace('"', '')
    return f'"{sanitized}"'


def parse_callout_block(lines: list[str]) -> Optional[CalloutBlock]:
    """Parses a contiguous run of blockquote `lines` (no trailing newlines,
    each already confirmed to match BLOCKQUOTE_LINE_PATTERN) as a callout,
    provided its first line is a callout header. Returns None if the block
    is just a plain blockquote (no `[!type]` header) — callers should leave
    those lines untouched rather than treat them as a callout."""
    header_match = CALLOUT_HEADER_PATTERN.match(lines[0])
    if not header_match:
        return None

    canonical_type, title = _resolve_canonical_type_and_title(
        header_match.group('type'), header_match.group('title')
    )

    body_lines = []
    for line in lines[1:]:
        body_match = BLOCKQUOTE_LINE_PATTERN.match(line)
        body_lines.append(body_match.group('rest'))

    fold = header_match.group('fold')
    return CalloutBlock(
        canonical_type=canonical_type,
        title=title,
        collapsible=fold in ('+', '-'),
        content='\n'.join(body_lines),
        initially_collapsed=fold == '-',
    )


def render_callout_as_jekyll_include(callout: CalloutBlock, index: int) -> str:
    """Renders a CalloutBlock as `{% capture %}` + `{% include callout.html %}`
    tags. `index` disambiguates the capture variable name across multiple
    callouts in the same file — Liquid capture variables aren't block-scoped,
    so a fixed shared name risks a later callout's capture clobbering an
    earlier one, e.g. if the two tags are ever reordered relative to each
    other during a future edit.

    `_includes/callout.html` doesn't need to exist for this output to be
    valid Liquid — Jekyll only resolves an `{% include %}` at site-build
    time, not when Liquid parses the tag.
    """
    var_name = f'callout_content_{index}'
    capture = f'{{% capture {var_name} %}}\n{callout.content}\n{{% endcapture %}}'
    include_parts = [
        f'type="{callout.canonical_type}"',
        f'title={_liquid_quote(callout.title)}',
        f'collapsible={"true" if callout.collapsible else "false"}',
    ]
    if callout.collapsible:
        include_parts.append(
            f'initially_collapsed={"true" if callout.initially_collapsed else "false"}'
        )
    include_parts.append(f'content={var_name}')
    include = '{% include callout.html ' + ' '.join(include_parts) + ' %}'
    return f'{capture}\n{include}'


def convert_obsidian_callouts_to_jekyll_includes(content: str) -> str:
    """
    Finds Obsidian-style callout blockquotes (`> [!type] Title` and their
    `>`-prefixed continuation lines) outside fenced ``` / ~~~ code blocks,
    and replaces each one with Jekyll `{% capture %}` + `{% include %}` tags
    (see render_callout_as_jekyll_include).

    A blockquote that does NOT start with a `[!type]` header (a plain quote)
    is left completely untouched, as is any blockquote-like text inside a
    fenced code block (e.g. a documentation example).

    Nested callouts (Obsidian's `>> [!type]` / `> > [!type]` syntax, any
    depth) are supported: once a callout's own body is extracted, it's just
    an ordinary markdown fragment again -- stripping one leading `>` from
    `>> [!bug] ...` leaves `> [!bug] ...`, which is indistinguishable from a
    fresh top-level callout. So each callout's content is recursively run
    back through this same conversion before being wrapped in its own
    `{% capture %}`. All levels of nesting share a single counter (see
    _convert_callouts_with_shared_counter) so two callouts never end up
    with the same capture variable name just because one happens to be
    nested inside another elsewhere in the file.
    """
    return _convert_callouts_with_shared_counter(content, itertools.count())


def _convert_callouts_with_shared_counter(content: str, counter: Iterator[int]) -> str:
    output_lines: list[str] = []
    pending_block: list[str] = []

    def flush_pending_block() -> None:
        if not pending_block:
            return
        callout = parse_callout_block(pending_block)
        if callout is None:
            output_lines.extend(pending_block)
        else:
            # Claim this callout's index before recursing, so capture
            # variable names read in roughly top-to-bottom document order
            # even though nested callouts (processed by the recursive call
            # below) end up with higher indices than their parent.
            index = next(counter)
            callout = callout._replace(
                content=_convert_callouts_with_shared_counter(callout.content, counter)
            )
            output_lines.append(render_callout_as_jekyll_include(callout, index))
        pending_block.clear()

    for fenced_line in iter_fenced_lines(content):
        if fenced_line.in_fence or fenced_line.is_fence_boundary:
            flush_pending_block()
            output_lines.append(fenced_line.line)
            continue

        if BLOCKQUOTE_LINE_PATTERN.match(fenced_line.line):
            pending_block.append(fenced_line.line)
        else:
            flush_pending_block()
            output_lines.append(fenced_line.line)

    flush_pending_block()
    return '\n'.join(output_lines)