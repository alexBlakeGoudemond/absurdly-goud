#!/usr/bin/env python3
"""
Converts Markdown image notation ![alt](src) into a Jekyll {% include
image.html %} tag.
"""

import re
from textwrap import dedent

from scripts.markdown_regions import apply_outside_fenced_blocks, apply_outside_inline_code

MARKDOWN_IMAGE_PATTERN = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')


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


def replace_images_in_segment(segment: str) -> str:
    def replace(match: re.Match) -> str:
        image_alt_text = match.group(1)
        image_name = match.group(2)
        return convert_markdown_image_notation_to_jekyll_includes_image_notation(
            image_name, image_alt_text
        )

    return MARKDOWN_IMAGE_PATTERN.sub(replace, segment)


def convert_images_outside_code(content: str) -> str:
    """
    Applies image-notation conversion only to text outside fenced '```' code
    blocks and inline `code` spans, so a documentation example showing
    ![alt](src) syntax isn't itself converted.
    """
    return apply_outside_fenced_blocks(
        content,
        lambda line: apply_outside_inline_code(line, replace_images_in_segment),
    )
