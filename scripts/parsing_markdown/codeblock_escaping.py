#!/usr/bin/env python3
"""
Wraps fenced (``` / ~~~) code blocks in Jekyll's {% raw %}...{% endraw %}
tags, so Liquid doesn't try to interpret template-like syntax that happens to
appear inside a code sample (e.g. a `{% ... %}` shown as an example).
"""

from scripts.parsing_markdown.markdown_regions import iter_fenced_lines


def escape_markdown_code_blocks_for_jekyll(content: str) -> str:
    output_lines = []

    for fenced_line in iter_fenced_lines(content):
        if fenced_line.fence_opened:
            output_lines.append('{% raw %}')
            output_lines.append(fenced_line.line)
        elif fenced_line.fence_closed:
            output_lines.append(fenced_line.line)
            output_lines.append('{% endraw %}')
        else:
            output_lines.append(fenced_line.line)

    return '\n'.join(output_lines)
