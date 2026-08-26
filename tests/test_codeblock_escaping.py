import unittest
from textwrap import dedent

from scripts.codeblock_escaping import escape_markdown_codeblocks_for_jekyll


class TestEscapeMarkdownCodeblocksForJekyll(unittest.TestCase):

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

    def test_content_with_no_fence_is_unchanged(self):
        content = "Just plain text with no special syntax."

        result = escape_markdown_codeblocks_for_jekyll(content)

        self.assertEqual(result, content)

    def test_content_outside_fence_is_left_untouched(self):
        content = dedent("""
        ![Alt text](image.png)
        ```
        code
        ```
        """)

        result = escape_markdown_codeblocks_for_jekyll(content)

        # This module only wraps fences now — image notation is untouched,
        # that's markdown_images' job.
        self.assertIn("![Alt text](image.png)", result)

    def test_blank_line_inside_fence_does_not_break_fence_tracking(self):
        content = dedent("""
        ```
        line one

        line two
        ```
        after
        """)

        result = escape_markdown_codeblocks_for_jekyll(content)

        self.assertIn("{% endraw %}", result)
        self.assertIn("after", result)

    def test_multiple_fenced_blocks_each_get_wrapped(self):
        content = dedent("""
        ```
        first
        ```
        text between
        ```
        second
        ```
        """)

        result = escape_markdown_codeblocks_for_jekyll(content)

        self.assertEqual(result.count("{% raw %}"), 2)
        self.assertEqual(result.count("{% endraw %}"), 2)


if __name__ == '__main__':
    unittest.main()
