import tempfile
import unittest
from pathlib import Path
from textwrap import dedent

import test_helpers
from test_helpers import register_synced_file
from scripts.parsing_markdown.markdown_excerpt import insert_excerpt_marker_after_first_paragraph
from scripts.parsing_markdown.wikilinks import build_note_path_lookup


class TestInsertExcerptMarkerAfterFirstParagraph(unittest.TestCase):
    """Unit tests for the pure string-transformation logic, independent of
    file I/O or the converter's orchestration."""

    def test_marker_is_inserted_between_first_and_second_paragraph(self):
        content = "Some text in markdown file\n\nSome text after paragraph"

        result = insert_excerpt_marker_after_first_paragraph(content)

        self.assertEqual(
            result,
            "Some text in markdown file\n\n<!--more-->\n\nSome text after paragraph",
        )

    def test_frontmatter_block_is_skipped_when_finding_first_paragraph(self):
        content = dedent("""\
            ---
            layout: default
            title: "Hello World"
            ---

            First paragraph of the note.

            Second paragraph.
            """)

        result = insert_excerpt_marker_after_first_paragraph(content)

        self.assertIn(
            "First paragraph of the note.\n\n<!--more-->\n\nSecond paragraph.",
            result,
        )
        # frontmatter itself must be untouched, not scanned for a "paragraph break"
        self.assertTrue(result.startswith('---\nlayout: default\ntitle: "Hello World"\n---\n\n'))

    def test_single_paragraph_content_is_left_unchanged(self):
        content = "Just one paragraph, nothing after it."

        result = insert_excerpt_marker_after_first_paragraph(content)

        self.assertEqual(result, content)
        self.assertNotIn("<!--more-->", result)

    def test_frontmatter_only_with_no_body_paragraphs_is_left_unchanged(self):
        content = "---\nlayout: default\n---\n\nOnly paragraph here."

        result = insert_excerpt_marker_after_first_paragraph(content)

        self.assertEqual(result, content)

    def test_already_present_marker_is_not_duplicated(self):
        content = "First paragraph.\n\n<!--more-->\n\nSecond paragraph.\n\nThird paragraph."

        result = insert_excerpt_marker_after_first_paragraph(content)

        self.assertEqual(result, content)
        self.assertEqual(result.count("<!--more-->"), 1)

    def test_multiple_blank_lines_between_paragraphs_place_excerpt_after_first_line_break(self):
        content = "First paragraph.\n\n\nSecond paragraph."

        result = insert_excerpt_marker_after_first_paragraph(content)

        self.assertEqual(result, "First paragraph.\n\n<!--more-->\n\n\nSecond paragraph.")

    def test_mid_file_horizontal_rule_is_not_mistaken_for_frontmatter(self):
        # A '---' later in the body (a markdown horizontal rule) must not be
        # confused with a closing frontmatter delimiter — only a leading
        # '---\n...\n---\n' block, right at the start of the file, counts.
        content = "First paragraph.\n\n---\n\nSecond paragraph after a horizontal rule."

        result = insert_excerpt_marker_after_first_paragraph(content)

        self.assertEqual(
            result,
            "First paragraph.\n\n<!--more-->\n\n---\n\nSecond paragraph after a horizontal rule.",
        )

    def test_single_heading_is_skipped_before_placing_marker(self):
        content = dedent("""\
            ## Website Name

            `ABsurdly Goud` is a personal website. Its name came from a few pieces of inspiration:

            - My initials are ABG - I wanted that included in the name""")

        result = insert_excerpt_marker_after_first_paragraph(content)

        self.assertEqual(result, dedent("""\
            ## Website Name

            `ABsurdly Goud` is a personal website. Its name came from a few pieces of inspiration:

            <!--more-->

            - My initials are ABG - I wanted that included in the name"""))

    def test_nested_headings_are_all_skipped_before_placing_marker(self):
        content = dedent("""\
            # Header 1

            ## Header 2

            ### Header 3

            #### Header 4

            some text is here

            more text is here""")

        result = insert_excerpt_marker_after_first_paragraph(content)

        self.assertEqual(result, dedent("""\
            # Header 1

            ## Header 2

            ### Header 3

            #### Header 4

            some text is here

            <!--more-->

            more text is here"""))

    def test_heading_with_no_paragraph_after_it_is_left_unchanged(self):
        content = "# Title\n\nOnly one paragraph after the title."

        result = insert_excerpt_marker_after_first_paragraph(content)

        self.assertEqual(result, content)
        self.assertNotIn("<!--more-->", result)

    def test_frontmatter_and_heading_are_both_skipped_before_placing_marker(self):
        content = dedent("""\
            ---
            layout: default
            ---

            ## Section

            First para.

            Second para.
            """)

        result = insert_excerpt_marker_after_first_paragraph(content)

        self.assertIn("First para.\n\n<!--more-->\n\nSecond para.", result)
        self.assertTrue(result.startswith("---\nlayout: default\n---\n\n## Section\n\n"))

    def test_heading_like_line_inside_a_paragraph_is_not_treated_as_a_heading(self):
        # A '#' only signals a heading when it's the entire block on its own
        # line — a line that merely starts with '#' inside running prose
        # (unusual, but possible) must not be skipped as if it were a title.
        content = "#hashtag mentioned inline is not a heading here.\n\nSecond paragraph."

        result = insert_excerpt_marker_after_first_paragraph(content)

        self.assertEqual(
            result,
            "#hashtag mentioned inline is not a heading here.\n\n<!--more-->\n\nSecond paragraph.",
        )


class TestAddExcerptMarkerToMarkdownFiles(unittest.TestCase):
    """Exercises the orchestration: add_excerpt_if_needed runs for every
    changed markdown file, after frontmatter has already been injected."""

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)
        self.converter = test_helpers.make_converter(Path(self.tmp_dir.name))
        self.converter.begin_run()
        self.note_lookup = build_note_path_lookup(Path(self.tmp_dir.name))
        self.image_lookup = {}

    def test_changed_markdown_file_gets_excerpt_marker_after_first_paragraph(self):
        dest = self.converter.output_location / "hello-world.md"
        dest.write_text(
            "Some text in markdown file\n\nSome text after paragraph",
            encoding="utf-8",
        )
        register_synced_file(self.converter, dest)

        self.converter.parse_markdown_files_for_jekyll(self.note_lookup, self.image_lookup)

        result = dest.read_text(encoding="utf-8")
        self.assertIn(
            "Some text in markdown file\n\n<!--more-->\n\nSome text after paragraph",
            result,
        )

    def test_excerpt_marker_lands_after_frontmatter_that_was_just_injected(self):
        # add_frontmatter_if_needed runs first in the pipeline, so by the time
        # add_excerpt_if_needed sees the file it must skip past that newly
        # added frontmatter block rather than inserting inside/before it.
        dest = self.converter.output_location / "hello-world.md"
        dest.write_text(
            "First real paragraph.\n\nSecond real paragraph.",
            encoding="utf-8",
        )
        register_synced_file(self.converter, dest)

        self.converter.parse_markdown_files_for_jekyll(self.note_lookup, self.image_lookup)

        result = dest.read_text(encoding="utf-8")
        self.assertIn("title: \"Hello World\"", result)
        self.assertIn(
            "First real paragraph.\n\n<!--more-->\n\nSecond real paragraph.",
            result,
        )
        # marker must come after the frontmatter's closing '---', not inside it
        frontmatter_close = result.index("---", result.index("---") + 3) + len("---")
        self.assertLess(frontmatter_close, result.index("<!--more-->"))

    def test_single_paragraph_file_gets_no_marker(self):
        dest = self.converter.output_location / "short-note.md"
        dest.write_text("Just one short paragraph.", encoding="utf-8")
        register_synced_file(self.converter, dest)

        self.converter.parse_markdown_files_for_jekyll(self.note_lookup, self.image_lookup)

        result = dest.read_text(encoding="utf-8")
        self.assertNotIn("<!--more-->", result)

    def test_cache_hit_file_not_in_changed_dest_paths_is_untouched(self):
        dest = self.converter.output_location / "post.md"
        original = "---\nlayout: default\ntitle: post\n---\n\nFirst.\n\nSecond."
        dest.write_text(original, encoding="utf-8")
        self.converter.site_sync.changed_dest_paths = []  # nothing changed this run

        self.converter.parse_markdown_files_for_jekyll(self.note_lookup, self.image_lookup)

        self.assertEqual(dest.read_text(encoding="utf-8"), original)


if __name__ == '__main__':
    unittest.main()
