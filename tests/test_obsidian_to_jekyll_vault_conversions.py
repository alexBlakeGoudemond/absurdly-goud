import unittest
import tempfile
from pathlib import Path
from textwrap import dedent

import test_helpers
from scripts.obsidian_to_jekyll import (
    ObsidianToJekyllConverter,
    convert_markdown_image_notation_to_jekyll_includes_image_notation,
    process_markdown_for_jekyll,
    escape_markdown_codeblocks_for_jekyll,
)


class TestExtractTitleFromFileName(unittest.TestCase):

    def test_strips_date_prefix_and_extension(self):
        title = ObsidianToJekyllConverter.extract_title_from_file_name("2026-08-19-hello-world.md")
        self.assertEqual(title, "hello-world")

    def test_no_date_prefix_still_strips_extension(self):
        title = ObsidianToJekyllConverter.extract_title_from_file_name("about.md")
        self.assertEqual(title, "about")

    def test_non_md_extension_is_untouched(self):
        title = ObsidianToJekyllConverter.extract_title_from_file_name("home.mdx")
        self.assertEqual(title, "home.mdx")


class TestAddFrontmatterToFile(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)
        self.tmp_path = Path(self.tmp_dir.name)

    def test_adds_default_layout_frontmatter(self):
        md_file = self.tmp_path / "2026-08-19-hello-world.md"
        md_file.write_text("# Hello World", encoding="utf-8")

        ObsidianToJekyllConverter.add_frontmatter_to_file(md_file)

        result = md_file.read_text(encoding="utf-8")
        self.assertIn("layout: default", result)
        self.assertIn("title: \"hello-world\"", result)
        self.assertIn("# Hello World", result)

    def test_permalink_included_when_requested(self):
        md_file = self.tmp_path / "about.md"
        md_file.write_text("About me", encoding="utf-8")

        ObsidianToJekyllConverter.add_frontmatter_to_file(md_file, include_permalink=True)

        result = md_file.read_text(encoding="utf-8")
        self.assertIn("permalink: /about/", result)

    def test_permalink_omitted_by_default(self):
        md_file = self.tmp_path / "post.md"
        md_file.write_text("Post body", encoding="utf-8")

        ObsidianToJekyllConverter.add_frontmatter_to_file(md_file)

        result = md_file.read_text(encoding="utf-8")
        self.assertNotIn("permalink:", result)

    def test_custom_layout_is_used(self):
        md_file = self.tmp_path / "post.md"
        md_file.write_text("Body", encoding="utf-8")

        ObsidianToJekyllConverter.add_frontmatter_to_file(md_file, file_layout="post")

        result = md_file.read_text(encoding="utf-8")
        self.assertIn("layout: post", result)


class TestAddFrontmatterToMarkdownFiles(unittest.TestCase):
    """Exercises the orchestration logic — which files get frontmatter injected
    based on changed_dest_paths, name, and extension — not add_frontmatter_to_file itself."""

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)
        self.converter = test_helpers.make_converter(Path(self.tmp_dir.name))
        self.converter.begin_run()

    def test_changed_markdown_file_gets_frontmatter(self):
        dest = self.converter.output_location / "hello-world.md"
        dest.write_text("# Hello", encoding="utf-8")
        self.converter.changed_dest_paths = [dest]

        self.converter.parse_markdown_files_for_jekyll()

        result = dest.read_text(encoding="utf-8")
        self.assertIn("layout: default", result)
        self.assertIn("title: \"hello-world\"", result)

    def test_about_md_gets_permalink(self):
        dest = self.converter.output_location / "about.md"
        dest.write_text("About me", encoding="utf-8")
        self.converter.changed_dest_paths = [dest]

        self.converter.parse_markdown_files_for_jekyll()

        result = dest.read_text(encoding="utf-8")
        self.assertIn("permalink: /about/", result)

    def test_ignored_files_are_skipped(self):
        for name in self.converter.IGNORED_FRONTMATTER_FILES:
            dest = self.converter.output_location / name
            dest.write_text("original content", encoding="utf-8")
            self.converter.changed_dest_paths = [dest]

            self.converter.parse_markdown_files_for_jekyll()

            self.assertEqual(dest.read_text(encoding="utf-8"), "original content")

    def test_non_markdown_files_are_skipped(self):
        dest = self.converter.output_location / "style.css"
        dest.write_text("body {}", encoding="utf-8")
        self.converter.changed_dest_paths = [dest]

        self.converter.parse_markdown_files_for_jekyll()

        self.assertEqual(dest.read_text(encoding="utf-8"), "body {}")

    def test_cache_hit_file_not_in_changed_dest_paths_is_untouched(self):
        # simulates a recurring run where this file was a cache hit (unchanged) —
        # it should NOT reappear in changed_dest_paths, and must not get double-frontmatter
        dest = self.converter.output_location / "post.md"
        original = "---\nlayout: default\ntitle: post\n---\n\nBody"
        dest.write_text(original, encoding="utf-8")
        self.converter.changed_dest_paths = []  # nothing changed this run

        self.converter.parse_markdown_files_for_jekyll()

        self.assertEqual(dest.read_text(encoding="utf-8"), original)

    def test_multiple_changed_files_all_get_processed(self):
        dest_a = self.converter.output_location / "post-a.md"
        dest_b = self.converter.output_location / "post-b.md"
        dest_a.write_text("A", encoding="utf-8")
        dest_b.write_text("B", encoding="utf-8")
        self.converter.changed_dest_paths = [dest_a, dest_b]

        self.converter.parse_markdown_files_for_jekyll()

        self.assertIn("title: \"post-a\"", dest_a.read_text(encoding="utf-8"))
        self.assertIn("title: \"post-b\"", dest_b.read_text(encoding="utf-8"))

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

    def test_process_one_markdown_image_yields_one_jekyll_includes_syntax_in_file(self):
        dest = self.converter.output_location / "post.md"
        dest.write_text("![Alt text](image.png)", encoding="utf-8")
        self.converter.changed_dest_paths = [dest]

        process_markdown_for_jekyll(dest)

        result = dest.read_text(encoding="utf-8")
        expected_syntax = """
        {% include image.html
            src="image.png"
            alt="Alt text"
            title="Alt text"
        %}
        """
        self.assertIn(dedent(expected_syntax), result)

    def test_process_two_markdown_image_yields_two_jekyll_includes_syntax_in_file(self):
        dest = self.converter.output_location / "post.md"
        dest.write_text("![Alt text 1](image1.png)\n![Alt text 2](image2.png)", encoding="utf-8")
        self.converter.changed_dest_paths = [dest]

        process_markdown_for_jekyll(dest)

        result = dest.read_text(encoding="utf-8")
        expected_syntax_1 = """
            {% include image.html
                src="image1.png"
                alt="Alt text 1"
                title="Alt text 1"
            %}
            """
        expected_syntax_2 = """
            {% include image.html
                src="image2.png"
                alt="Alt text 2"
                title="Alt text 2"
            %}
            """
        self.assertIn(dedent(expected_syntax_1), result)
        self.assertIn(dedent(expected_syntax_2), result)


class TestEscapeMarkdownCodeblocksForJekyll(unittest.TestCase):
    """Covers fence detection, raw-wrapping, and image-conversion suppression
    inside fenced code blocks and inline code spans."""

    def test_fenced_code_block_is_wrapped_in_raw_tags(self):
        content = dedent("""
        ```
        some code
        ```
        """)

        result = escape_markdown_codeblocks_for_jekyll(content)

        self.assertIn("{% raw %}\n```", result)
        self.assertIn("```\n{% endraw %}", result)

    def test_fenced_block_with_language_tag_is_wrapped(self):
        content = dedent("""
        ```python
        print('hi')
        ```
        """)

        result = escape_markdown_codeblocks_for_jekyll(content)

        self.assertIn("{% raw %}\n```python", result)
        self.assertIn("```\n{% endraw %}", result)

    def test_tilde_fence_is_wrapped(self):
        content = dedent("""
        ~~~
        some code
        ~~~
        """)

        result = escape_markdown_codeblocks_for_jekyll(content)

        self.assertIn("{% raw %}\n~~~", result)
        self.assertIn("~~~\n{% endraw %}", result)

    def test_image_syntax_inside_fenced_block_is_not_converted(self):
        content = dedent("""
        ```
        ![Alt text](image.png)
        ```
        """)

        result = escape_markdown_codeblocks_for_jekyll(content)

        self.assertIn("![Alt text](image.png)", result)
        self.assertNotIn("{% include image.html", result)

    def test_image_syntax_outside_fence_is_still_converted(self):
        content = dedent("""
        ![Alt text](image.png)
        ```
        code
        ```
        """)

        result = escape_markdown_codeblocks_for_jekyll(content)

        self.assertIn("{% include image.html", result)

    def test_image_syntax_inside_inline_code_span_is_not_converted(self):
        content = "Use `![Alt text](image.png)` syntax for images."

        result = escape_markdown_codeblocks_for_jekyll(content)

        self.assertIn("`![Alt text](image.png)`", result)
        self.assertNotIn("{% include image.html", result)

    def test_two_images_on_same_line_are_both_converted(self):
        content = "![Alt one](one.png) and ![Alt two](two.png)"

        result = escape_markdown_codeblocks_for_jekyll(content)

        self.assertIn('src="one.png"', result)
        self.assertIn('alt="Alt one"', result)
        self.assertIn('src="two.png"', result)
        self.assertIn('alt="Alt two"', result)

    def test_blank_line_inside_fence_does_not_break_fence_tracking(self):
        content = dedent("""
        ```
        line one

        line two
        ```
        ![Alt](img.png)
        """)

        result = escape_markdown_codeblocks_for_jekyll(content)

        self.assertIn("{% include image.html", result)
        self.assertIn("{% endraw %}", result)

    def test_content_with_no_fence_or_image_is_unchanged(self):
        content = "Just plain text with no special syntax."

        result = escape_markdown_codeblocks_for_jekyll(content)

        self.assertEqual(result, content)


if __name__ == '__main__':
    unittest.main()
