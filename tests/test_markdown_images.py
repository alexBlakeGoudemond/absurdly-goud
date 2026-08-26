import unittest
from textwrap import dedent

from scripts.markdown_images import (
    convert_markdown_image_notation_to_jekyll_includes_image_notation,
    convert_images_outside_code,
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

        result = convert_images_outside_code(content)

        self.assertIn('{% include image.html', result)
        self.assertIn('src="image.png"', result)
        self.assertIn('alt="Alt text"', result)

    def test_two_images_on_same_line_are_both_converted(self):
        content = "![Alt one](one.png) and ![Alt two](two.png)"

        result = convert_images_outside_code(content)

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

        result = convert_images_outside_code(content)

        self.assertIn("![Alt text](image.png)", result)
        self.assertNotIn("{% include image.html", result)

    def test_image_syntax_outside_fence_is_still_converted(self):
        content = dedent("""
        ![Alt text](image.png)
        ```
        code
        ```
        """)

        result = convert_images_outside_code(content)

        self.assertIn("{% include image.html", result)

    def test_image_syntax_inside_inline_code_span_is_not_converted(self):
        content = "Use `![Alt text](image.png)` syntax for images."

        result = convert_images_outside_code(content)

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

        result = convert_images_outside_code(content)

        self.assertIn("{% include image.html", result)


if __name__ == '__main__':
    unittest.main()
