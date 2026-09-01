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

from scripts.parsing_markdown.markdown_regions import apply_outside_code_blocks_and_code_spans

# A Markdown link or image: [text](url). Deliberately matches just this
# `[...](...)` shape -- by the time this runs, Obsidian's own `![[img]]` and
# `[[Note]]` syntaxes have already been converted to it (or to Jekyll
# includes), so this single pattern covers everything left: plain links,
# and the `[Alt Text]({% link ... %}...)` output of wikilink conversion.
MARKDOWN_LINK_PATTERN = re.compile(r'\[([^\]]*)\]\(([^)]+)\)')

# A `|` not already preceded by a backslash, so a pipe someone already
# escaped by hand (`\|`) is left alone instead of becoming `\\|`.
UNESCAPED_PIPE_PATTERN = re.compile(r'(?<!\\)\|')


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
    return apply_outside_code_blocks_and_code_spans(content, escape_pipes_in_markdown_links)
