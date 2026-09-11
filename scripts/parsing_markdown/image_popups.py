#!/usr/bin/env python3
"""
Loads popup metadata (source link + blurb + optional preview image) for
inline images from a vault data file, e.g.
absurdly-goud-obsidian/data/image_popups.yml:

    image_popups:
      - image_vault: "assets/88x31/buttons-memes/free-real-estate.gif"
        image_source: "https://knowyourmeme.com/memes/free-real-estate"
        image_preview: "https://knowyourmeme.com/photos/original.jpg"
        popup_blurb: "Cloning the repo is basically free real estate."

Entries are keyed by the image_vault filename (matching how
build_image_path_lookup resolves images), so any inline image not listed
here simply gets no entry — the caller decides the fallback.
"""

from pathlib import Path
import re

import yaml

DEFAULT_POPUP_BLURB = "No details yet"
DEFAULT_POPUP_REDIRECT_TEXT = "Learn more"

# Deliberately permissive on query params (e.g. ?si=..., &t=30s) since real
# links people paste in rarely come as bare watch?v=ID URLs.
YOUTUBE_ID_PATTERN = re.compile(
    r'(?:youtube(?:-nocookie)?\.com/(?:watch\?(?:.*&)?v=|embed/|shorts/)|youtu\.be/)'
    r'(?P<id>[A-Za-z0-9_-]{11})'
)
VIMEO_ID_PATTERN = re.compile(r'vimeo\.com/(?:video/)?(?P<id>\d+)')
VIDEO_FILE_EXTENSIONS = {'.mp4', '.webm', '.mov', '.ogg', '.ogv'}


def classify_preview_type(raw_value: str) -> str:
    """Classifies a raw image_preview value (local vault path or URL) as
    'youtube', 'vimeo', 'video' (a direct video file), or 'image' — the
    default, covering plain image paths/URLs and anything unrecognized."""
    lower_value = raw_value.lower()
    if 'youtube.com' in lower_value or 'youtu.be' in lower_value:
        return 'youtube'
    if 'vimeo.com' in lower_value:
        return 'vimeo'
    if Path(raw_value).suffix.lower() in VIDEO_FILE_EXTENSIONS:
        return 'video'
    return 'image'


def build_youtube_embed_url(raw_value: str) -> str | None:
    """Extracts the video ID from any common YouTube URL shape and returns
    a youtube-nocookie.com embed URL (fewer tracking cookies set before any
    interaction). Returns None if no valid-looking ID is found, so the
    caller can fall back gracefully rather than embedding a broken iframe."""
    match = YOUTUBE_ID_PATTERN.search(raw_value)
    return f'https://www.youtube-nocookie.com/embed/{match.group("id")}' if match else None


def build_vimeo_embed_url(raw_value: str) -> str | None:
    match = VIMEO_ID_PATTERN.search(raw_value)
    return f'https://player.vimeo.com/video/{match.group("id")}' if match else None


def load_image_popup_entries(data_path: Path) -> dict[str, dict]:
    """Load image_popups.yml from disk, or return an empty dict if the file
    is missing, empty, corrupt, or doesn't contain an image_popups: list —
    mirroring website_manifest.load_manifest's tolerance for a missing or
    broken data file so a build never crashes on this being absent."""
    if not data_path.exists():
        return {}

    try:
        raw = yaml.safe_load(data_path.read_text(encoding="utf-8"))
    except yaml.YAMLError:
        print(f"Warning: image popup data at '{data_path}' is corrupt, ignoring.")
        return {}

    if not isinstance(raw, dict):
        return {}

    popup_list = raw.get("image_popups")
    if not isinstance(popup_list, list):
        return {}

    entries: dict[str, dict] = {}
    for entry in popup_list:
        if not isinstance(entry, dict) or "image_vault" not in entry:
            continue

        filename = Path(entry["image_vault"]).name
        entries[filename] = {
            "image_source": entry.get("image_source"),
            "image_preview": entry.get("image_preview"),
            "popup_blurb": entry.get("popup_blurb"),
            "popup_redirect_text": entry.get("popup_redirect_text") or DEFAULT_POPUP_REDIRECT_TEXT,
        }

    return entries