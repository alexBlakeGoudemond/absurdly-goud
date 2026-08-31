import tempfile
import unittest
from pathlib import Path
from textwrap import dedent

from scripts.parsing_markdown.wikilinks import (
    build_note_path_lookup,
    convert_wikilinks_to_jekyll_layout,
    convert_wikilink_note_links_outside_code_blocks_and_code_spans,
)


class TestBuildNotePathLookup(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)
        self.tmp_path = Path(self.tmp_dir.name)

    def test_duplicate_note_name_across_folders_raises(self):
        (self.tmp_path / "a").mkdir()
        (self.tmp_path / "b").mkdir()
        (self.tmp_path / "a" / "Note.md").write_text("")
        (self.tmp_path / "b" / "Note.md").write_text("")

        with self.assertRaises(ValueError) as context:
            build_note_path_lookup(self.tmp_path)

        self.assertIn("Note", str(context.exception))

    def test_unique_note_names_build_a_lookup(self):
        (self.tmp_path / "First.md").write_text("")
        (self.tmp_path / "Second.md").write_text("")

        lookup = build_note_path_lookup(self.tmp_path)

        self.assertEqual(lookup, {"First": "First.md", "Second": "Second.md"})


class TestWikilinksConvertedToJekyllLayout(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)
        tmp_path = Path(self.tmp_dir.name)

        # Create the notes these tests expect to resolve against
        (tmp_path / "LinkedNote.md").write_text("")
        (tmp_path / "linked-note.md").write_text("")

        self.note_lookup = build_note_path_lookup(Path(self.tmp_dir.name))

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
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)
        tmp_path = Path(self.tmp_dir.name)
        (tmp_path / "LinkedNote.md").write_text("")
        self.note_lookup = build_note_path_lookup(tmp_path)

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
