#!/usr/bin/env python3
"""
Resolves Obsidian-style [[wikilinks]] into Jekyll {% link %} tags.
"""

import re
from pathlib import Path

from scripts.parsing_markdown.markdown_regions import apply_outside_code_blocks_and_code_spans

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


def build_note_path_lookup(new_manifest: dict, output_location: Path) -> dict[str, str]:
    """
    Builds a lookup of `note name` -> `path relative to output_location`,
    using forward slashes so it can be dropped straight into a Jekyll
    {% link %} tag.

    Built from a SiteSync manifest (self.site_sync.new_manifest), keyed by
    each note's ORIGINAL (source/vault) filename stem — not by scanning the
    output tree and using each file's own stem there. This matters because
    copy_vault_resources() slugifies filenames on the way into _posts/ (see
    filenames.slugify_filename), so a post's output stem no longer matches
    the title a wikilink actually references, e.g. a vault note named
    'My Post Title.md' lands as '_posts/.../my-post-title.md'. A wikilink
    written as [[My Post Title]] needs to resolve against the ORIGINAL name;
    only the manifest (which records both source and dest per entry) has
    that mapping. Scanning the output tree can only ever recover the dest
    name, which is exactly the one wikilinks don't reference.

    Must run AFTER all copying, since site_sync.sync_file records a manifest
    entry for every file each run — changed or an unchanged cache hit —
    so an unchanged note is still available here as a valid wikilink target
    for a note that did change this run.

    Assumes note names are unique across the vault, mirroring how Obsidian
    itself resolves [[wikilinks]] (by basename, regardless of folder).
    """
    lookup: dict[str, str] = {}

    for entry in new_manifest.values():
        source_path = Path(entry["source"])
        if source_path.suffix != ".md":
            continue

        note_name = source_path.stem
        dest_path = Path(entry["dest"])
        relative_path = dest_path.relative_to(output_location).as_posix()

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


def convert_wikilink_note_links_outside_code_blocks_and_code_spans(content: str, note_path_lookup: dict[str, str]) -> str:
    """
    Applies convert_wikilinks_to_jekyll_layout only to text outside fenced '```'
    code blocks and inline `code` spans. Without this, a documentation example
    like `` `[[...]]` `` or a ```markdown sample containing [[Note]] gets
    treated as a real link and fails lookup.
    """
    def convert_segment(segment: str) -> str:
        return convert_wikilinks_to_jekyll_layout(segment, note_path_lookup)

    return apply_outside_code_blocks_and_code_spans(content, convert_segment)