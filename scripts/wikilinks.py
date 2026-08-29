#!/usr/bin/env python3
"""
Resolves Obsidian-style [[wikilinks]] into Jekyll {% link %} tags.
"""

import re
from pathlib import Path

from scripts.markdown_regions import apply_outside_code_block

# Matches Obsidian wikilinks: [[NoteName#NoteSubSection|AltText]]
# Both #NoteSubSection and |AltText are optional.
WIKILINK_PATTERN = re.compile(
    r"""
    \[\[
        (?P<note>[^\]#|]+)             # NoteName            (required)
        (?: \# (?P<section>[^\]|]+) )? # #NoteSubSection     (optional)
        (?: \| (?P<alt>[^\]]+) )?      # |AltText            (optional)
    \]\]
    """,
    re.VERBOSE,
)


def build_note_path_lookup(notes_path: Path) -> dict[str, str]:
    """
    Scans `notes_path` (the OUTPUT tree, i.e. self.output_location, not the vault)
    and builds a lookup of `note name` -> `path relative to notes_path`, using forward
    slashes so it can be dropped straight into a Jekyll {% link %} tag.

    Must run against the output tree because copy_vault_resources() renames
    the vault's posts/ folder to _posts/ on the way out — resolving against
    the vault would produce links pointing at a path that no longer exists.

    Assumes note names are unique across the vault, mirroring how Obsidian
    itself resolves [[wikilinks]] (by basename, regardless of folder).
    """
    lookup: dict[str, str] = {}

    for md_file in notes_path.rglob("*.md"):
        note_name = md_file.stem
        relative_path = md_file.relative_to(notes_path).as_posix()

        if note_name in lookup:
            raise ValueError(
                f"Duplicate note name '{note_name}' found at both "
                f"'{lookup[note_name]}' and '{relative_path}'. "
                "Wikilink resolution requires unique note names across the site."
            )

        lookup[note_name] = relative_path

    return lookup


def slugify(text: str) -> str:
    """Mimics kramdown's auto-generated heading anchors: lowercase, spaces to hyphens."""
    return text.strip().lower().replace(" ", "-")


def convert_wikilinks_to_jekyll_layout(content: str, note_path_lookup: dict[str, str]) -> str:
    """
    Converts Obsidian-style wikilinks into a Jekyll {% link %} layout, resolving
    each note name to its real path in the output tree via note_path_lookup
    (see build_note_path_lookup).

    [[Note]]                       -> [Note]({% link path/to/Note.md %})
    [[Note#Sub Section]]           -> [Note]({% link path/to/Note.md %}#sub-section)
    [[Note|Alt Text]]              -> [Alt Text]({% link path/to/Note.md %})
    [[Note#Sub Section|Alt Text]]  -> [Alt Text]({% link path/to/Note.md %}#sub-section)
    """

    def replace(match: re.Match) -> str:
        note, section, alt = match.groupdict().values()
        note = note.strip()

        try:
            note_path = note_path_lookup[note]
        except KeyError:
            raise ValueError(
                f"Wikilink references unknown note '{note}'. "
                "Check the note exists in the vault/output tree and the lookup is current."
            ) from None

        link_text = alt.strip() if alt else note
        anchor = f"#{slugify(section)}" if section else ""

        return f"[{link_text}]({{% link {note_path} %}}{anchor})"

    return WIKILINK_PATTERN.sub(replace, content)


def convert_wikilinks_outside_code(content: str, note_path_lookup: dict[str, str]) -> str:
    """
    Applies convert_wikilinks_to_jekyll_layout only to text outside fenced '```'
    code blocks and inline `code` spans. Without this, a documentation example
    like `` `[[...]]` `` or a ```markdown sample containing [[Note]] gets
    treated as a real link and fails lookup.
    """
    def convert_segment(segment: str) -> str:
        return convert_wikilinks_to_jekyll_layout(segment, note_path_lookup)

    return apply_outside_code_block(content, convert_segment)
