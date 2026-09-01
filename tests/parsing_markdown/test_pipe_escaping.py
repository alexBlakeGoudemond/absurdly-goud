import unittest
from textwrap import dedent

from scripts.parsing_markdown.pipe_escaping import (
    escape_pipes,
    escape_pipes_in_markdown_links,
    escape_pipes_in_links_outside_code_blocks_and_code_spans,
)


class TestEscapePipes(unittest.TestCase):

    def test_bare_pipe_is_escaped(self):
        self.assertEqual(escape_pipes("a | b"), r"a \| b")

    def test_multiple_pipes_are_all_escaped(self):
        self.assertEqual(escape_pipes("a | b | c"), r"a \| b \| c")

    def test_already_escaped_pipe_is_left_alone(self):
        # Not doubled into `\\|` -- a hand-escaped pipe is idempotent.
        self.assertEqual(escape_pipes(r"a \| b"), r"a \| b")

    def test_text_without_pipe_is_unchanged(self):
        self.assertEqual(escape_pipes("no pipes here"), "no pipes here")


class TestEscapePipesInMarkdownLinks(unittest.TestCase):

    def test_pipe_in_link_text_is_escaped(self):
        # The exact case from the bug report.
        content = "[Wikilink | with pipe](https://blot.im/how/formatting/wikilinks)"

        result = escape_pipes_in_markdown_links(content)

        self.assertEqual(
            result,
            r"[Wikilink \| with pipe](https://blot.im/how/formatting/wikilinks)"
        )

    def test_pipe_in_url_is_escaped(self):
        content = "[Link](https://example.com/page?a=1|b=2)"

        result = escape_pipes_in_markdown_links(content)

        self.assertEqual(result, r"[Link](https://example.com/page?a=1\|b=2)")

    def test_link_without_pipe_is_unchanged(self):
        content = "[Wikilink without pipe](https://blot.im/how/formatting/wikilinks)"

        result = escape_pipes_in_markdown_links(content)

        self.assertEqual(result, content)

    def test_pipe_outside_a_link_is_left_untouched(self):
        # Deliberately scoped: a stray `|` in plain prose, unrelated to any
        # link, isn't this function's job -- keeps real Markdown tables
        # elsewhere on the site from getting mangled.
        content = "Pipes | in prose are not touched here."

        result = escape_pipes_in_markdown_links(content)

        self.assertEqual(result, content)

    def test_multiple_links_on_one_line_are_both_escaped(self):
        content = "[One | pipe](url1) and [Two | pipes | here](url2)"

        result = escape_pipes_in_markdown_links(content)

        self.assertEqual(
            result,
            r"[One \| pipe](url1) and [Two \| pipes \| here](url2)"
        )

    def test_already_escaped_pipe_in_link_is_not_double_escaped(self):
        content = r"[Already \| escaped](url)"

        result = escape_pipes_in_markdown_links(content)

        self.assertEqual(result, content)

    def test_image_syntax_pipe_is_also_escaped(self):
        # By the time this step runs, real `![alt](src)` syntax has already
        # been converted to a Jekyll include, but the pattern is shape-only
        # and would just as happily fix a pipe here too if one slipped through.
        content = "![Alt | text](image.png)"

        result = escape_pipes_in_markdown_links(content)

        self.assertEqual(result, r"![Alt \| text](image.png)")


class TestEscapePipesInLinksOutsideCode(unittest.TestCase):

    def test_pipe_in_link_outside_code_is_escaped(self):
        content = "[Wikilink | with pipe](https://blot.im/how/formatting/wikilinks)"

        result = escape_pipes_in_links_outside_code_blocks_and_code_spans(content)

        self.assertIn(r"Wikilink \| with pipe", result)

    def test_pipe_in_link_inside_fenced_block_is_not_escaped(self):
        content = dedent("""
        ```
        [Wikilink | with pipe](url)
        ```
        """)

        result = escape_pipes_in_links_outside_code_blocks_and_code_spans(content)

        self.assertIn("[Wikilink | with pipe](url)", result)
        self.assertNotIn(r"\|", result)

    def test_pipe_in_link_inside_inline_code_span_is_not_escaped(self):
        content = "Example: `[Wikilink | with pipe](url)`"

        result = escape_pipes_in_links_outside_code_blocks_and_code_spans(content)

        self.assertIn("`[Wikilink | with pipe](url)`", result)

    def test_real_link_outside_fence_alongside_example_inside_fence(self):
        content = dedent("""
        [Real | link](url1)
        ```
        [Example | link](url2)
        ```
        """)

        result = escape_pipes_in_links_outside_code_blocks_and_code_spans(content)

        self.assertIn(r"[Real \| link](url1)", result)
        self.assertIn("[Example | link](url2)", result)


if __name__ == '__main__':
    unittest.main()
