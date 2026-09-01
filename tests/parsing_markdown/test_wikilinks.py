import tempfile
import unittest
from pathlib import Path
from textwrap import dedent

from scripts.parsing_markdown.wikilinks import (
    build_note_path_lookup,
    convert_wikilinks_to_jekyll_layout,
    convert_wikilink_note_links_outside_code_blocks_and_code_spans,
)


def manifest_entry(source: str, dest: str) -> dict:
    """Builds a manifest entry with the fields build_note_path_lookup reads
    (source, dest); sha256/last_published are irrelevant to that function
    but included so the shape matches a real SiteSync entry."""
    return {"source": source, "dest": dest, "sha256": "test-hash", "last_published": "2026-08-29 12:00"}


class TestBuildNotePathLookup(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)
        self.tmp_path = Path(self.tmp_dir.name)
        self.output_location = self.tmp_path / "output"

    def test_duplicate_note_name_across_folders_raises(self):
        manifest = {
            "/vault/a/Note.md": manifest_entry("/vault/a/Note.md", str(self.output_location / "a" / "Note.md")),
            "/vault/b/Note.md": manifest_entry("/vault/b/Note.md", str(self.output_location / "b" / "Note.md")),
        }

        with self.assertRaises(ValueError) as context:
            build_note_path_lookup(manifest, self.output_location)

        self.assertIn("Note", str(context.exception))

    def test_unique_note_names_build_a_lookup(self):
        manifest = {
            "/vault/First.md": manifest_entry("/vault/First.md", str(self.output_location / "First.md")),
            "/vault/Second.md": manifest_entry("/vault/Second.md", str(self.output_location / "Second.md")),
        }

        lookup = build_note_path_lookup(manifest, self.output_location)

        self.assertEqual(lookup, {"First": "First.md", "Second": "Second.md"})

    def test_lookup_key_is_the_original_source_stem_not_the_slugified_dest_stem(self):
        # Regression test: copy_vault_resources() slugifies post filenames
        # on the way into _posts/ (e.g. via slugify_filename), so a post's
        # OUTPUT stem no longer matches the title a wikilink references.
        # The lookup must be keyed by the note's original vault name.
        source = "/vault/posts/2026-08-31 88x31 Exploration.md"
        dest = str(self.output_location / "_posts" / "2026-08-31-88x31-exploration.md")
        manifest = {source: manifest_entry(source, dest)}

        lookup = build_note_path_lookup(manifest, self.output_location)

        self.assertEqual(
            lookup,
            {"2026-08-31 88x31 Exploration": "_posts/2026-08-31-88x31-exploration.md"}
        )

    def test_non_markdown_manifest_entries_are_ignored(self):
        manifest = {
            "/vault/img.png": manifest_entry("/vault/img.png", str(self.output_location / "assets" / "img.png")),
            "/vault/Note.md": manifest_entry("/vault/Note.md", str(self.output_location / "Note.md")),
        }

        lookup = build_note_path_lookup(manifest, self.output_location)

        self.assertEqual(lookup, {"Note": "Note.md"})

    def test_empty_manifest_yields_empty_lookup(self):
        lookup = build_note_path_lookup({}, self.output_location)

        self.assertEqual(lookup, {})


class TestWikilinksConvertedToJekyllLayout(unittest.TestCase):

    def setUp(self):
        # These tests only exercise convert_wikilinks_to_jekyll_layout, which
        # just consumes a note_path_lookup dict -- built directly here rather
        # than round-tripped through build_note_path_lookup's manifest shape,
        # which is covered separately by TestBuildNotePathLookup.
        self.note_lookup = {
            "LinkedNote": "LinkedNote.md",
            "linked-note": "linked-note.md",
        }

    def test_wikilinks_are_converted_to_jekyll_layout(self):
        content1 = "[[LinkedNote]]"
        content2 = "[[linked-note]]"

        result1 = convert_wikilinks_to_jekyll_layout(content1, self.note_lookup)
        result2 = convert_wikilinks_to_jekyll_layout(content2, self.note_lookup)

        self.assertIn("[LinkedNote]({% link LinkedNote.md %})", result1)
        self.assertIn("[linked-note]({% link linked-note.md %})", result2)

    def test_wikilinks_with_subsections_are_converted_to_jekyll_layout(self):
        content1 = "[[LinkedNote#The Subsection]]"
        content2 = "[[linked-note#The Subsection]]"

        result1 = convert_wikilinks_to_jekyll_layout(content1, self.note_lookup)
        result2 = convert_wikilinks_to_jekyll_layout(content2, self.note_lookup)

        self.assertIn("[LinkedNote]({% link LinkedNote.md %}#the-subsection)", result1)
        self.assertIn("[linked-note]({% link linked-note.md %}#the-subsection)", result2)

    def test_wikilinks_with_alt_text_are_converted_to_jekyll_layout(self):
        content1 = "[[LinkedNote|A Summary]]"
        content2 = "[[linked-note|a summary]]"

        result1 = convert_wikilinks_to_jekyll_layout(content1, self.note_lookup)
        result2 = convert_wikilinks_to_jekyll_layout(content2, self.note_lookup)

        self.assertIn("[A Summary]({% link LinkedNote.md %})", result1)
        self.assertIn("[a summary]({% link linked-note.md %})", result2)

    def test_wikilinks_with_alt_text_with_subsections_are_converted_to_jekyll_layout(self):
        content1 = "[[LinkedNote#The Subsection|A Summary]]"
        content2 = "[[linked-note#The Subsection|a summary]]"

        result1 = convert_wikilinks_to_jekyll_layout(content1, self.note_lookup)
        result2 = convert_wikilinks_to_jekyll_layout(content2, self.note_lookup)

        self.assertIn("[A Summary]({% link LinkedNote.md %}#the-subsection)", result1)
        self.assertIn("[a summary]({% link linked-note.md %}#the-subsection)", result2)

    def test_unknown_note_raises_value_error(self):
        content = "[[NoSuchNote]]"

        with self.assertRaises(ValueError) as context:
            convert_wikilinks_to_jekyll_layout(content, self.note_lookup)

        self.assertIn("NoSuchNote", str(context.exception))


class TestConvertWikilinksOutsideCode(unittest.TestCase):
    """Covers fence and inline-code suppression specifically — the wikilink
    equivalent of the image-suppression tests in test_markdown_images.py."""

    def setUp(self):
        self.note_lookup = {"LinkedNote": "LinkedNote.md"}

    def test_wikilink_outside_code_is_converted(self):
        content = "[[LinkedNote]]"

        result = convert_wikilink_note_links_outside_code_blocks_and_code_spans(content, self.note_lookup)

        self.assertIn("{% link LinkedNote.md %}", result)

    def test_wikilink_inside_fenced_block_is_not_resolved(self):
        # An example wikilink shown inside a code sample should not be treated
        # as a real link — a real link there would fail lookup for arbitrary
        # example note names anyway.
        content = dedent("""
        ```markdown
        [[SomeExampleNote]]
        ```
        """)

        result = convert_wikilink_note_links_outside_code_blocks_and_code_spans(content, self.note_lookup)

        self.assertIn("[[SomeExampleNote]]", result)
        self.assertNotIn("{% link", result)

    def test_wikilink_inside_inline_code_span_is_not_resolved(self):
        content = "Use `[[NoteName]]` syntax for links."

        result = convert_wikilink_note_links_outside_code_blocks_and_code_spans(content, self.note_lookup)

        self.assertIn("`[[NoteName]]`", result)
        self.assertNotIn("{% link", result)

    def test_real_wikilink_outside_fence_alongside_example_inside_fence(self):
        content = dedent("""
        [[LinkedNote]]
        ```
        [[SomeExampleNote]]
        ```
        """)

        result = convert_wikilink_note_links_outside_code_blocks_and_code_spans(content, self.note_lookup)

        self.assertIn("{% link LinkedNote.md %}", result)
        self.assertIn("[[SomeExampleNote]]", result)


if __name__ == '__main__':
    unittest.main()