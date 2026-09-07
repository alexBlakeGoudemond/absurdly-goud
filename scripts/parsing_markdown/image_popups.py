#!/usr/bin/env python3
"""
Loads popup metadata (source link + blurb) for inline images from a vault
data file, e.g. absurdly-goud-obsidian/data/image_popups.yml:

    image_popups:
      - image_vault: "assets/88x31/buttons-memes/free-real-estate.gif"
        image_source: "https://knowyourmeme.com/memes/free-real-estate"
        popup_blurb: "Cloning the repo is basically free real estate."

Entries are keyed by the image_vault filename (matching how
build_image_path_lookup resolves images), so any inline image not listed
here simply gets no entry — the caller decides the fallback.
"""

from pathlib import Path

import yaml

DEFAULT_POPUP_BLURB = "No details yet"


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
            "popup_blurb": entry.get("popup_blurb"),
        }

    return entries
