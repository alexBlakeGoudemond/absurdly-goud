import unittest
from textwrap import dedent

from scripts.markdown_regions import (
    iter_fenced_lines,
    apply_outside_inline_code_span, apply_outside_code_block,
)


class TestIterFencedLines(unittest.TestCase):

    def test_plain_content_has_no_fenced_lines(self):
        content = "just some text\nand more text"

        results = list(iter_fenced_lines(content))

        self.assertTrue(all(not r.in_fence and not r.is_fence_boundary for r in results))

    def test_backtick_fence_open_and_close_are_flagged(self):
        content = dedent("""\
        ```
        code
        ```""")

        results = list(iter_fenced_lines(content))

        self.assertTrue(results[0].fence_opened)
        self.assertTrue(results[1].in_fence)
        self.assertFalse(results[1].is_fence_boundary)
        self.assertTrue(results[2].fence_closed)

    def test_tilde_fence_open_and_close_are_flagged(self):
        content = dedent("""\
        ~~~
        code
        ~~~""")

        results = list(iter_fenced_lines(content))

        self.assertTrue(results[0].fence_opened)
        self.assertTrue(results[2].fence_closed)

    def test_mismatched_fence_marker_does_not_close_fence(self):
        # A ~~~ line inside an open ``` fence doesn't close it — it's just content,
        # matching Markdown/kramdown fence semantics.
        content = dedent("""\
        ```
        ~~~
        still code
        ```""")

        results = list(iter_fenced_lines(content))

        self.assertTrue(results[0].fence_opened)
        self.assertTrue(results[1].in_fence)
        self.assertFalse(results[1].is_fence_boundary)
        self.assertTrue(results[2].in_fence)
        self.assertTrue(results[3].fence_closed)

    def test_fence_with_language_tag_is_detected(self):
        content = "```python"

        result = next(iter(iter_fenced_lines(content)))

        self.assertTrue(result.fence_opened)

    def test_unclosed_fence_stays_open_to_end_of_content(self):
        content = dedent("""\
        ```
        code that never closes""")

        results = list(iter_fenced_lines(content))

        self.assertTrue(results[0].fence_opened)
        self.assertTrue(results[1].in_fence)


class TestApplyOutsideFencedBlocks(unittest.TestCase):

    def test_transform_applied_outside_fence(self):
        content = "before\nafter"

        result = apply_outside_code_block(content, lambda line: line.upper())

        self.assertEqual(result, "BEFORE\nAFTER")

    def test_transform_not_applied_inside_fence(self):
        content = dedent("""\
        before
        ```
        inside
        ```
        after""")

        result = apply_outside_code_block(content, lambda line: line.upper())

        self.assertIn("inside", result)  # untouched, not "INSIDE"
        self.assertIn("BEFORE", result)
        self.assertIn("AFTER", result)

    def test_fence_delimiter_lines_are_never_transformed(self):
        content = dedent("""\
        ```python
        inside
        ```""")

        result = apply_outside_code_block(content, lambda line: line.upper())

        self.assertIn("```python", result)


class TestApplyOutsideInlineCode(unittest.TestCase):

    def test_transform_applied_outside_inline_code(self):
        line = "before `code` after"

        result = apply_outside_inline_code_span(line, lambda segment: segment.upper())

        self.assertEqual(result, "BEFORE `code` AFTER")

    def test_multiple_inline_code_spans_all_preserved(self):
        line = "`one` middle `two`"

        result = apply_outside_inline_code_span(line, lambda segment: segment.upper())

        self.assertEqual(result, "`one` MIDDLE `two`")

    def test_no_inline_code_transforms_whole_line(self):
        line = "plain text"

        result = apply_outside_inline_code_span(line, lambda segment: segment.upper())

        self.assertEqual(result, "PLAIN TEXT")


if __name__ == '__main__':
    unittest.main()
