#!/usr/bin/env python3
"""
Filename-safety helpers for the Jekyll output tree.

Jekyll's post-naming convention requires `_posts` filenames to be
`YYYY-MM-DD-title.md` — lowercase, hyphen-separated, no spaces — or Jekyll
will misparse or silently skip the post entirely. Obsidian note titles are
free-form ("2026-08-27 Vision Whiteboard Showing.md"), so this converts one
into the other.
"""

from pathlib import Path


def slugify_filename(filename: str) -> str:
    """`2026-08-27 Vision Whiteboard Showing.md` -> `2026-08-27-vision-whiteboard-showing.md`.
    Lowercases and replace the spaces with hyphens in the stem; the extension
    and any characters that are already hyphens (e.g. in the date) are left
    untouched."""
    original_path = Path(filename)
    slug = original_path.stem.strip().lower().replace(" ", "-")
    return f"{slug}{original_path.suffix}"
