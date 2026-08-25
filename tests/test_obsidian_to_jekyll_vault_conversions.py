import unittest
from textwrap import dedent

from scripts.obsidian_to_jekyll import (
    ObsidianToJekyllConverter,
    convert_markdown_image_notation_to_jekyll_includes_image_notation,
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


class TestMarkdownImageNotationConversion(unittest.TestCase):

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

    def test_content_with_no_fence_or_image_is_unchanged(self):
        content = "Just plain text with no special syntax."

        result = escape_markdown_codeblocks_for_jekyll(content)

        self.assertEqual(result, content)


class TestEscapeMarkdownCodeblocksAndImageNotationConversion(unittest.TestCase):
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


if __name__ == '__main__':
    unittest.main()
