#!/usr/bin/env python3
"""
Converts Markdown image notation ![alt](src) into a Jekyll {% include
image.html %} tag.
"""

import re
from pathlib import Path
from textwrap import dedent

from scripts.markdown_regions import apply_outside_code_blocks_and_code_spans

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


def build_image_path_lookup(assets_path: Path) -> dict[str, str]:
    """
    Scans `assets_path` (the OUTPUT tree's assets/ dir, i.e.
    self.output_location / 'assets') and builds a lookup of `image filename`
    -> `path relative to assets_path's parent`, using forward slashes so it
    can be dropped straight into a Jekyll image src.

    Needed because copy_vault_images_into_assets_directory() buckets images
    by their top-level vault directory (e.g. 'assets/88x31', 'assets/posts')
    rather than a single flat 'assets/images' folder, so a bare filename like
    'free-real-estate.svg' is no longer enough on its own to locate the file
    — the bucket has to be resolved too.

    Assumes image filenames are unique across the vault, mirroring how
    Obsidian's own ![[image.png]] embed syntax resolves images by filename
    alone, regardless of folder.
    """
    lookup: dict[str, str] = {}
    output_location = assets_path.parent

    for image_file in assets_path.rglob("*"):
        if not image_file.is_file():
            continue

        relative_path = image_file.relative_to(output_location).as_posix()

        if image_file.name in lookup:
            raise ValueError(
                f"Duplicate image filename '{image_file.name}' found at both "
                f"'{lookup[image_file.name]}' and '{relative_path}'. "
                "Image resolution requires unique filenames across the vault."
            )

        lookup[image_file.name] = relative_path

    return lookup


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


def replace_images_in_segment(segment: str, image_path_lookup: dict[str, str]) -> str:
    def replace(match: re.Match) -> str:
        image_alt_text = match.group(1)
        image_name = match.group(2)
        # Only a bare local filename (e.g. 'free-real-estate.svg', produced by
        # the wikilink-embed conversion above) is resolved against the vault's
        # assets bucket. An external URL is left exactly as written even if
        # its basename happens to collide with a known asset's filename —
        # otherwise a remote image could get silently rewritten to point at
        # an unrelated local file.
        if '://' in image_name:
            image_src = image_name
        else:
            image_src = image_path_lookup.get(Path(image_name).name, image_name)
        return convert_markdown_image_notation_to_jekyll_includes_image_notation(
            image_src, image_alt_text
        )

    return MARKDOWN_IMAGE_PATTERN.sub(replace, segment)


def convert_markdown_image_embeds_outside_code_blocks_and_code_spans(
        content: str, image_path_lookup: dict[str, str]
) -> str:
    """
    Applies image-notation conversion only to text outside fenced '```' code
    blocks and inline `code` spans, so a documentation example showing
    ![alt](src) syntax isn't itself converted.

    image_path_lookup resolves each bare image
    filename to its real bucketed path under assets/, so the emitted src
    actually locates the file post-move.
    """

    def convert_segment(segment: str) -> str:
        return replace_images_in_segment(segment, image_path_lookup)

    return apply_outside_code_blocks_and_code_spans(content, convert_segment)


def replace_wikilink_image_embeds_in_segment(segment: str) -> str:
    def replace(match: re.Match) -> str:
        name = match.group('name')
        return f'![{name}]({name})'

    return WIKILINK_IMAGE_PATTERN.sub(replace, segment)


def convert_wikilink_image_embeds_outside_code_blocks_and_code_spans(content: str) -> str:
    """
    Rewrites Obsidian's image embed syntax, `![[image.png]]`, into standard
    Markdown image notation (`![image.png](image.png)`) so it flows
    into a normal Jekyll image include, the same as any other image.

    Must run BEFORE converting wikilinks outside fenced code blocks because:
    a `[[...]]` immediately preceded by `!` would otherwise be caught by the
    generic wikilink pattern and treated as a note link — which then fails the
    lookup, since it's an image filename, not a note name.
    """
    return apply_outside_code_blocks_and_code_spans(content, replace_wikilink_image_embeds_in_segment)
