import tempfile
import unittest
from pathlib import Path
from textwrap import dedent

from scripts.parsing_markdown.markdown_images import (
    build_image_path_lookup,
    convert_markdown_image_notation_to_jekyll_includes_image_notation,
    convert_markdown_image_embeds_outside_code_blocks_and_code_spans,
    convert_wikilink_image_embeds_outside_code_blocks_and_code_spans,
)


class TestCreateJekyllImageLayout(unittest.TestCase):

    def test_markdown_image_notation_gets_converted_to_jekyll_includes_file(self):
        actual_syntax = convert_markdown_image_notation_to_jekyll_includes_image_notation('image.png', 'Alt text')
        expected_syntax = """
        {% include image.html
            src="image.png"
            alt="Alt text"
            title="Alt text"
        %}
        """
        self.assertEqual(dedent(expected_syntax), actual_syntax)


class TestConvertImagesOutsideCode(unittest.TestCase):
    """Covers plain conversion plus fence/inline-code suppression, which used
    to live inside escape_markdown_codeblocks_for_jekyll's tests before image
    conversion became its own module."""

    def test_image_syntax_is_converted(self):
        content = "![Alt text](image.png)"

        result = convert_markdown_image_embeds_outside_code_blocks_and_code_spans(content, {})

        self.assertIn('{% include image.html', result)
        self.assertIn('src="image.png"', result)
        self.assertIn('alt="Alt text"', result)

    def test_two_images_on_same_line_are_both_converted(self):
        content = "![Alt one](one.png) and ![Alt two](two.png)"

        result = convert_markdown_image_embeds_outside_code_blocks_and_code_spans(content, {})

        self.assertIn('src="one.png"', result)
        self.assertIn('alt="Alt one"', result)
        self.assertIn('src="two.png"', result)
        self.assertIn('alt="Alt two"', result)

    def test_image_syntax_inside_fenced_block_is_not_converted(self):
        content = dedent("""
        ```
        ![Alt text](image.png)
        ```
        """)

        result = convert_markdown_image_embeds_outside_code_blocks_and_code_spans(content, {})

        self.assertIn("![Alt text](image.png)", result)
        self.assertNotIn("{% include image.html", result)

    def test_image_syntax_outside_fence_is_still_converted(self):
        content = dedent("""
        ![Alt text](image.png)
        ```
        code
        ```
        """)

        result = convert_markdown_image_embeds_outside_code_blocks_and_code_spans(content, {})

        self.assertIn("{% include image.html", result)

    def test_image_syntax_inside_inline_code_span_is_not_converted(self):
        content = "Use `![Alt text](image.png)` syntax for images."

        result = convert_markdown_image_embeds_outside_code_blocks_and_code_spans(content, {})

        self.assertIn("`![Alt text](image.png)`", result)
        self.assertNotIn("{% include image.html", result)

    def test_blank_line_inside_fence_does_not_break_fence_tracking(self):
        content = dedent("""
        ```
        line one

        line two
        ```
        ![Alt](img.png)
        """)

        result = convert_markdown_image_embeds_outside_code_blocks_and_code_spans(content, {})

        self.assertIn("{% include image.html", result)

    def test_bare_filename_is_resolved_via_image_path_lookup(self):
        # A bare filename matching a known asset gets rewritten to its
        # bucketed path — this is what lets image.html find the file after
        # copy_vault_images_into_assets_directory buckets it by top-level
        # vault directory instead of a single flat assets/images folder.
        content = "![Alt text](free-real-estate.svg)"
        lookup = {"free-real-estate.svg": "assets/88x31/free-real-estate.svg"}

        result = convert_markdown_image_embeds_outside_code_blocks_and_code_spans(content, lookup)

        self.assertIn('src="assets/88x31/free-real-estate.svg"', result)

    def test_unresolvable_src_is_left_unchanged(self):
        # A src the lookup doesn't recognize — e.g. an external URL — is
        # passed through untouched rather than mangled.
        content = "![Alt text](https://example.com/image.png)"
        lookup = {"image.png": "assets/88x31/image.png"}

        result = convert_markdown_image_embeds_outside_code_blocks_and_code_spans(content, lookup)

        self.assertIn('src="https://example.com/image.png"', result)


class TestBuildImagePathLookup(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)
        self.output_location = Path(self.tmp_dir.name)
        self.assets_path = self.output_location / "assets"

    def test_bucketed_image_resolves_to_its_full_relative_path(self):
        bucket = self.assets_path / "88x31"
        bucket.mkdir(parents=True)
        (bucket / "free-real-estate.svg").write_text("<svg></svg>", encoding="utf-8")

        lookup = build_image_path_lookup(self.assets_path)

        self.assertEqual(lookup["free-real-estate.svg"], "assets/88x31/free-real-estate.svg")

    def test_root_level_asset_resolves_without_a_bucket(self):
        self.assets_path.mkdir(parents=True)
        (self.assets_path / "favicon.svg").write_text("<svg></svg>", encoding="utf-8")

        lookup = build_image_path_lookup(self.assets_path)

        self.assertEqual(lookup["favicon.svg"], "assets/favicon.svg")

    def test_duplicate_filename_across_buckets_raises(self):
        (self.assets_path / "posts").mkdir(parents=True)
        (self.assets_path / "88x31").mkdir(parents=True)
        (self.assets_path / "posts" / "photo.png").write_bytes(b"one")
        (self.assets_path / "88x31" / "photo.png").write_bytes(b"two")

        with self.assertRaises(ValueError):
            build_image_path_lookup(self.assets_path)

    def test_missing_assets_directory_returns_empty_lookup(self):
        lookup = build_image_path_lookup(self.assets_path)

        self.assertEqual(lookup, {})


class TestConvertWikilinkImageEmbedsOutsideCode(unittest.TestCase):
    """Covers Obsidian's own ![[image.png]] embed syntax — distinct from
    standard ![alt](src) markdown and from [[NoteName]] wikilinks."""

    def test_wikilink_image_embed_is_converted_to_markdown_image_syntax(self):
        content = "![[theImage.png]]"

        result = convert_wikilink_image_embeds_outside_code_blocks_and_code_spans(content)

        self.assertEqual(result, "![theImage.png](theImage.png)")

    def test_size_hint_is_dropped(self):
        content = "![[theImage.png|300]]"

        result = convert_wikilink_image_embeds_outside_code_blocks_and_code_spans(content)

        self.assertEqual(result, "![theImage.png](theImage.png)")

    def test_non_image_embed_is_left_untouched(self):
        # ![[SomeNote]] (no image extension) is Obsidian note transclusion,
        # a different feature this function deliberately doesn't touch.
        content = "![[SomeNote]]"

        result = convert_wikilink_image_embeds_outside_code_blocks_and_code_spans(content)

        self.assertEqual(result, "![[SomeNote]]")

    def test_embed_inside_properly_closed_inline_code_is_left_untouched(self):
        content = "Curious to see if Wikilink images work: `![[theImage.png]]`"

        result = convert_wikilink_image_embeds_outside_code_blocks_and_code_spans(content)

        self.assertIn("`![[theImage.png]]`", result)
        self.assertNotIn("![theImage.png](theImage.png)", result)

    def test_embed_inside_fenced_block_is_left_untouched(self):
        content = dedent("""
        ```
        ![[theImage.png]]
        ```
        """)

        result = convert_wikilink_image_embeds_outside_code_blocks_and_code_spans(content)

        self.assertIn("![[theImage.png]]", result)
        self.assertNotIn("![theImage.png](theImage.png)", result)

    def test_unclosed_backtick_is_not_treated_as_code_and_is_converted(self):
        # A single unmatched backtick isn't a real inline code span by
        # Markdown's own rules, so this is genuine prose and should convert —
        # this is exactly the case that used to crash with a ValueError.
        content = "Curious to see if Wikilink images work: `![[theImage.png]]"

        result = convert_wikilink_image_embeds_outside_code_blocks_and_code_spans(content)

        self.assertIn("![theImage.png](theImage.png)", result)


if __name__ == '__main__':
    unittest.main()
