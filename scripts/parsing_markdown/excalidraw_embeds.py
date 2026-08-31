#!/usr/bin/env python3
"""
Handles Obsidian's Excalidraw notes. A note named `<name>.excalidraw.md`
holds the drawing's raw scene JSON in its body — not something we want (or
are able) to render ourselves. Instead, we rely on Obsidian's Excalidraw
plugin "auto-export SVG" setting, which writes a rendered sibling file,
`<name>.excalidraw.svg`, into the vault next to the note on every save.

This module's job is narrow: fully replace ("swap") the note's body with a
single Markdown image reference to that sibling SVG, so the existing
markdown_images conversion picks it up and turns it into a normal Jekyll
image include.
"""

from pathlib import Path

EXCALIDRAW_NOTE_SUFFIX = ".excalidraw.md"


def is_excalidraw_note(markdown_file: Path) -> bool:
    return markdown_file.name.endswith(EXCALIDRAW_NOTE_SUFFIX)


def excalidraw_svg_filename(markdown_file: Path) -> str:
    """`vision-diagram.excalidraw.md` -> `vision-diagram.excalidraw.svg`,
    matching the filename Obsidian's Excalidraw auto-export writes next to
    the note (same basename, `.md` swapped for `.svg`)."""
    return markdown_file.name.removesuffix(".md") + ".svg"


def swap_excalidraw_note_with_image_embed(markdown_file: Path) -> None:
    """Replaces the ENTIRE contents of an *.excalidraw.md note (Obsidian's
    embedded drawing JSON, plus any Excalidraw-plugin frontmatter) with a
    single markdown image reference to the auto-exported SVG.

    Must run BEFORE frontmatter injection (add_frontmatter_to_file) — this
    overwrites the whole file rather than editing the body, so if frontmatter
    were added first, this would wipe it out again.
    """
    svg_filename = excalidraw_svg_filename(markdown_file)
    markdown_file.write_text(f"![{svg_filename}]({svg_filename})\n", encoding="utf-8")
