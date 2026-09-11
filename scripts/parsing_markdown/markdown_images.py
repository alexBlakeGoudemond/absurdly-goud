#!/usr/bin/env python3
"""
Converts Markdown image notation ![alt](src) into a Jekyll {% include
image.html %} tag.
"""

import re
from pathlib import Path
from textwrap import dedent

from scripts.parsing_markdown.markdown_regions import apply_outside_code_blocks_and_code_spans
from scripts.parsing_markdown.image_popups import (
    DEFAULT_POPUP_BLURB,
    DEFAULT_POPUP_REDIRECT_TEXT,
    classify_preview_type,
    build_youtube_embed_url,
    build_vimeo_embed_url,
)

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


def convert_markdown_image_notation_to_jekyll_includes_image_notation(
        image_name: str, image_alt_text: str, is_inline: bool = True,
        popup_source: str | None = None, popup_blurb: str | None = None,
        popup_preview: str | None = None, popup_preview_type: str | None = None,
        popup_redirect_text: str | None = None,
) -> str:
    opening_brace = '{%'
    closing_brace = '%}'

    if is_inline:
        # An inline image always gets a popup (unlike a figure, which never
        # does) — falling back to a self-link (the image's own resolved
        # path) and a default blurb when there's no image_popups.yml entry
        # behind it, rather than omitting the popup attributes. The popup's
        # preview falls back to the displayed image itself (always a plain
        # image, hence popup_preview_type defaults to 'image' too) when no
        # separate original/bigger preview is supplied.
        resolved_popup_source = popup_source if popup_source is not None else image_name
        resolved_popup_blurb = popup_blurb if popup_blurb is not None else DEFAULT_POPUP_BLURB
        resolved_popup_preview = popup_preview if popup_preview is not None else image_name
        resolved_popup_preview_type = popup_preview_type if popup_preview_type is not None else 'image'
        resolved_popup_redirect_text = (
            popup_redirect_text if popup_redirect_text is not None else DEFAULT_POPUP_REDIRECT_TEXT
        )

        # Single line, no leading/trailing newlines — must sit inline with
        # surrounding prose without breaking the paragraph/list item or
        # risking kramdown misreading indentation as a code block.
        return (
            f'{opening_brace} include image.html '
            f'src="{image_name}" alt="{image_alt_text}" title="{image_alt_text}" '
            f'popup_src="{resolved_popup_source}" popup_blurb="{resolved_popup_blurb}" '
            f'popup_redirect_text="{resolved_popup_redirect_text}" '
            f'popup_preview="{resolved_popup_preview}" popup_preview_type="{resolved_popup_preview_type}" '
            f'{closing_brace}'
        )

    jekyll_image_layout_notation = f"""
        {opening_brace} include figure.html
            src="{image_name}"
            alt="{image_alt_text}"
            title="{image_alt_text}"
        {closing_brace}
        """
    return dedent(jekyll_image_layout_notation)


def replace_images_in_line(
        line: str, image_path_lookup: dict[str, str],
        image_popup_lookup: dict[str, dict] | None = None,
) -> str:
    matches = list(MARKDOWN_IMAGE_PATTERN.finditer(line))
    if len(matches) > 1:
        is_inline = True
    elif len(matches) == 1:
        remainder = MARKDOWN_IMAGE_PATTERN.sub('', line).strip()
        is_inline = bool(remainder)  # anything left over means it's embedded in prose
    else:
        is_inline = False  # unused, no match to replace anyway

    def resolve_popup(image_name: str) -> tuple[str | None, str | None, str | None, str | None, str | None]:
        if not image_popup_lookup:
            return None, None, None, None, None
        popup_entry = image_popup_lookup.get(Path(image_name).name)
        if not popup_entry:
            return None, None, None, None, None

        def resolve_local_or_external(raw_path: str | None) -> str | None:
            if not raw_path:
                return None
            if '://' in raw_path:
                return raw_path  # external URL, passed through as-is
            # Local vault path: resolve through the same bucketed lookup as
            # the display image, so it points at where the file actually
            # landed post-build rather than its vault-relative path.
            return image_path_lookup.get(Path(raw_path).name, raw_path)

        def resolve_preview(raw_preview: str | None) -> tuple[str | None, str | None]:
            if not raw_preview:
                return None, None

            preview_type = classify_preview_type(raw_preview)
            if preview_type == 'youtube':
                embed_url = build_youtube_embed_url(raw_preview)
                if embed_url:
                    return embed_url, 'youtube'
                # Looked like a YouTube link but no video ID could be
                # extracted — fall back to treating it as a plain image
                # rather than embedding a guaranteed-broken iframe.
                return resolve_local_or_external(raw_preview), 'image'
            if preview_type == 'vimeo':
                embed_url = build_vimeo_embed_url(raw_preview)
                if embed_url:
                    return embed_url, 'vimeo'
                return resolve_local_or_external(raw_preview), 'image'

            # 'video' (a direct local/hosted file) and 'image' both go
            # through the same local-vs-external resolution as image_source.
            return resolve_local_or_external(raw_preview), preview_type

        popup_source = resolve_local_or_external(popup_entry.get('image_source'))
        popup_blurb = popup_entry.get('popup_blurb')
        popup_preview, popup_preview_type = resolve_preview(popup_entry.get('image_preview'))
        popup_redirect_text = popup_entry.get('popup_redirect_text') or DEFAULT_POPUP_REDIRECT_TEXT

        return popup_source, popup_blurb, popup_preview, popup_preview_type, popup_redirect_text

    def replace(match: re.Match) -> str:
        image_alt_text = match.group(1)
        image_name = match.group(2)
        if '://' in image_name:
            image_src = image_name
        else:
            image_src = image_path_lookup.get(Path(image_name).name, image_name)

        popup_source, popup_blurb, popup_preview, popup_preview_type, popup_redirect_text = resolve_popup(image_name)

        return convert_markdown_image_notation_to_jekyll_includes_image_notation(
            image_src, image_alt_text, is_inline=is_inline,
            popup_source=popup_source, popup_blurb=popup_blurb,
            popup_preview=popup_preview, popup_preview_type=popup_preview_type,
            popup_redirect_text=popup_redirect_text,
        )

    return MARKDOWN_IMAGE_PATTERN.sub(replace, line)


def convert_markdown_image_embeds_outside_code_blocks_and_code_spans(
        content: str, image_path_lookup: dict[str, str],
        image_popup_lookup: dict[str, dict] | None = None,
) -> str:
    """
    Applies image-notation conversion only to text outside fenced '```' code
    blocks and inline `code` spans, so a documentation example showing
    ![alt](src) syntax isn't itself converted.

    image_path_lookup resolves each bare image
    filename to its real bucketed path under assets/, so the emitted src
    actually locates the file post-move. image_popup_lookup (optional)
    supplies each inline image's popup source/blurb from image_popups.yml.
    """

    def convert_segment(segment: str) -> str:
        return replace_images_in_line(segment, image_path_lookup, image_popup_lookup)

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