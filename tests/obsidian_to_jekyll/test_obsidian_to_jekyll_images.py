import tempfile
import unittest
from pathlib import Path
from textwrap import dedent

import test_helpers
from scripts.obsidian_to_jekyll import (
    process_markdown_for_jekyll,
)


class TestMarkdownImageNotationConversion(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)
        self.tmp_path = Path(self.tmp_dir.name)
        self.converter = test_helpers.make_converter(Path(self.tmp_dir.name))
        self.converter.begin_run()
        self.note_lookup = {}
        self.image_lookup = {}

    def test_process_one_markdown_image_yields_one_jekyll_includes_syntax_in_file(self):
        dest = self.converter.output_location / "post.md"
        dest.write_text("![Alt text](image.png)", encoding="utf-8")
        self.converter.site_sync.changed_dest_paths = [dest]

        process_markdown_for_jekyll(dest, self.note_lookup, self.image_lookup)

        result = dest.read_text(encoding="utf-8")
        expected_syntax = """
        {% include figure.html
            src="image.png"
            alt="Alt text"
            title="Alt text"
        %}
        """
        self.assertIn(dedent(expected_syntax), result)

    def test_process_two_markdown_image_yields_two_jekyll_includes_syntax_in_file(self):
        dest = self.converter.output_location / "post.md"
        dest.write_text("![Alt text 1](image1.png)\n![Alt text 2](image2.png)", encoding="utf-8")
        self.converter.site_sync.changed_dest_paths = [dest]

        process_markdown_for_jekyll(dest, self.note_lookup, self.image_lookup)

        result = dest.read_text(encoding="utf-8")
        expected_syntax_1 = """
            {% include figure.html
                src="image1.png"
                alt="Alt text 1"
                title="Alt text 1"
            %}
            """
        expected_syntax_2 = """
            {% include figure.html
                src="image2.png"
                alt="Alt text 2"
                title="Alt text 2"
            %}
            """
        self.assertIn(dedent(expected_syntax_1), result)
        self.assertIn(dedent(expected_syntax_2), result)

    def test_wikilink_style_image_embed_does_not_crash_and_becomes_a_real_image(self):
        # Regression test: ![[theImage.png]] used to be caught by the plain
        # [[...]] wikilink pattern and crash with "unknown note" — an image
        # filename was never a valid note to look up in the first place.
        dest = self.converter.output_location / "post.md"
        dest.write_text(
            "Curious to see if Wikilink images work: `![[theImage.png]]",  # deliberately unclosed backtick
            encoding="utf-8",
        )
        self.converter.site_sync.changed_dest_paths = [dest]

        process_markdown_for_jekyll(dest, self.note_lookup, self.image_lookup)  # must not raise

        result = dest.read_text(encoding="utf-8")
        self.assertIn("{% include image.html", result)
        self.assertIn('src="theImage.png"', result)

    def test_image_src_is_resolved_to_its_bucketed_path(self):
        # Mirrors what run() actually does: image_path_lookup is built from
        # the real assets/ tree, so a note referencing a bare filename ends
        # up with a src that locates the file post-bucketing.
        dest = self.converter.output_location / "post.md"
        dest.write_text("![Alt text](free-real-estate.svg)", encoding="utf-8")
        self.converter.site_sync.changed_dest_paths = [dest]
        self.image_lookup = {"free-real-estate.svg": "assets/88x31/free-real-estate.svg"}

        process_markdown_for_jekyll(dest, self.note_lookup, self.image_lookup)

        result = dest.read_text(encoding="utf-8")
        self.assertIn('src="assets/88x31/free-real-estate.svg"', result)

    def test_wikilink_style_image_embed_inside_real_inline_code_is_left_as_text(self):
        dest = self.converter.output_location / "post.md"
        dest.write_text(
            "Example syntax: `![[theImage.png]]`",  # properly closed this time
            encoding="utf-8",
        )
        self.converter.site_sync.changed_dest_paths = [dest]

        process_markdown_for_jekyll(dest, self.note_lookup, self.image_lookup)  # must not raise

        result = dest.read_text(encoding="utf-8")
        self.assertIn("`![[theImage.png]]`", result)
        self.assertNotIn("{% include image.html", result)


if __name__ == '__main__':
    unittest.main()
