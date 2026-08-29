#!/usr/bin/env python3
"""
Converts Markdown image notation ![alt](src) into a Jekyll {% include
image.html %} tag.
"""

import re
from textwrap import dedent

from scripts.markdown_regions import apply_outside_code_block

MARKDOWN_IMAGE_PATTERN = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')

# Obsidian's own embed syntax: ![[image.png]], optionally with a display-width
# hint like ![[image.png|300]]. Deliberately restricted to known image
# extensions (matching what the rest of the pipeline already recognizes as an
# image) so a non-image embed, e.g. ![[SomeNote]] transclusion, is left alone
# rather than silently mishandled here.
WIKILINK_IMAGE_PATTERN = re.compile(
    r'!\[\[(?P<name>[^\]|#]+\.(?:png|jpe?g|gif|svg))(?:\|[^\]]*)?\]\]',
    re.IGNORECASE,
)


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
    return apply_outside_code_block(content, replace_images_in_segment)


def replace_wikilink_image_embeds_in_segment(segment: str) -> str:
    def replace(match: re.Match) -> str:
        name = match.group('name')
        return f'![{name}]({name})'

    return WIKILINK_IMAGE_PATTERN.sub(replace, segment)


def convert_wikilink_image_embeds_outside_code(content: str) -> str:
    """
    Rewrites Obsidian's image embed syntax, `![[image.png]]`, into standard
    markdown image notation (`![image.png](image.png)`) so it flows through
    convert_images_outside_code into a normal Jekyll image include, the same
    as any other image.

    Must run BEFORE wikilinks.convert_wikilinks_outside_code in the pipeline:
    a `[[...]]` immediately preceded by `!` would otherwise be caught by the
    generic wikilink pattern and treated as a note link — which then fails
    lookup, since it's an image filename, not a note name.
    """
    return apply_outside_code_block(content, replace_wikilink_image_embeds_in_segment)
