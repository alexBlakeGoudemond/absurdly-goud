import tempfile
import unittest
from pathlib import Path
from textwrap import dedent

from scripts.obsidian_to_jekyll import process_markdown_for_jekyll
from scripts.parsing_markdown.codeblock_escaping import escape_markdown_code_blocks_for_jekyll
from scripts.parsing_markdown.markdown_images import (
    convert_markdown_image_embeds_outside_code_blocks_and_code_spans,
    convert_wikilink_image_embeds_outside_code_blocks_and_code_spans,
)
from scripts.parsing_markdown.pipe_escaping import (
    escape_pipes_in_links_outside_code_blocks_and_code_spans,
)
from scripts.parsing_markdown.wikilinks import (
    convert_wikilink_note_links_outside_code_blocks_and_code_spans,
)


class TestEscapeMarkdownTablesForJekyll(unittest.TestCase):
    """
    Verifies that markdown table column pipes are preserved while bare pipes
    inside markdown link text/urls within table cells are escaped.
    """

    def test_plain_markdown_table_pipes_are_preserved(self):
        content = dedent("""
        | Header 1 | Header 2 | Header 3 |
        | :--- | :---: | ---: |
        | Cell 1 | Cell 2 | Cell 3 |
        | Alpha | Beta | Gamma |
        """).strip()

        result = escape_pipes_in_links_outside_code_blocks_and_code_spans(content)

        expected = dedent("""
        
        | Header 1 | Header 2 | Header 3 |
        | :--- | :---: | ---: |
        | Cell 1 | Cell 2 | Cell 3 |
        | Alpha | Beta | Gamma |
        
        """)
        self.assertEqual(result, expected)

    def test_markdown_link_with_pipe_inside_table_cell_is_escaped(self):
        content = dedent("""
        | Name | Link | Description |
        | --- | --- | --- |
        | Site | [Site | Home](https://example.com) | Welcome |
        """).strip()

        result = escape_pipes_in_links_outside_code_blocks_and_code_spans(content)

        expected = dedent(r"""
        
        | Name | Link | Description |
        | --- | --- | --- |
        | Site | [Site \| Home](https://example.com) | Welcome |
        
        """)
        self.assertEqual(result, expected)

    def test_markdown_link_with_pipe_in_url_inside_table_cell_is_escaped(self):
        content = dedent("""
        | Query | Link |
        | --- | --- |
        | Filter | [Search](https://example.com/search?a=1|b=2) |
        """).strip()

        result = escape_pipes_in_links_outside_code_blocks_and_code_spans(content)

        expected = dedent(r"""
        
        | Query | Link |
        | --- | --- |
        | Filter | [Search](https://example.com/search?a=1\|b=2) |
        
        """)
        self.assertEqual(result, expected)

    def test_already_escaped_pipe_in_table_cell_link_is_not_double_escaped(self):
        content = dedent(r"""
        | Name | Link |
        | --- | --- |
        | Guide | [User \| Manual](https://example.com) |
        """).strip()

        result = escape_pipes_in_links_outside_code_blocks_and_code_spans(content)

        expected = dedent(r"""
        
        | Name | Link |
        | --- | --- |
        | Guide | [User \| Manual](https://example.com) |
        
        """)
        self.assertEqual(result, expected)

    def test_inline_code_span_with_pipes_inside_table_cell_is_not_escaped(self):
        content = dedent("""
        | Feature | Syntax |
        | --- | --- |
        | Regex | `cat | dog` |
        | Command | `ls -la | grep py` |
        """).strip()

        result = escape_pipes_in_links_outside_code_blocks_and_code_spans(content)

        expected = dedent("""
        
        | Feature | Syntax |
        | --- | --- |
        | Regex | `cat | dog` |
        | Command | `ls -la | grep py` |
        
        """)
        self.assertEqual(result, expected)

    def test_single_row_table_without_newlines_around_it_have_newlines_added(self):
        content = dedent("""
        Tight text above
        | Query | Link |
        | --- | --- |
        | Filter | [Search](https://example.com) |
        Tight text below
        """).strip()

        result = escape_pipes_in_links_outside_code_blocks_and_code_spans(content)

        expected = dedent(r"""
        Tight text above

        | Query | Link |
        | --- | --- |
        | Filter | [Search](https://example.com) |

        Tight text below
        """).strip()
        self.assertEqual(result, expected)
        self.assertTrue(result.__contains__("\n\n| Query |"))
        self.assertTrue(result.__contains__("| [Search](https://example.com) |\n\n"))

    def test_multi_row_table_without_newlines_around_it_have_newlines_added(self):
        content = dedent("""
        Tight text above
        | bob |
        | --- |
        | cat1 |
        | cat2 |
        | cat3 |
        Tight text below
        """).strip()

        result = escape_pipes_in_links_outside_code_blocks_and_code_spans(content)

        expected = dedent(r"""
        Tight text above

        | bob |
        | --- |
        | cat1 |
        | cat2 |
        | cat3 |

        Tight text below
        """).strip()
        self.assertEqual(result, expected)
        self.assertTrue(result.__contains__("\n\n| bob |"))
        self.assertTrue(result.__contains__("| cat3 |\n\n"))

    def test_table_followed_by_paragraph_containing_piped_link_has_newlines_added(self):
        content = dedent("""
        a fish
        | bob |
        | --- |
        | cat |
        | cat |
        A video popped into my feed that I liked, about guestbooks: [Veronika Explains | Guestbook](https://youtu.be/ZSBYO1BYrDM?si=TL2T-jEKnaiFY-sN).
        """).strip()

        result = escape_pipes_in_links_outside_code_blocks_and_code_spans(content)

        expected = dedent(r"""
        a fish

        | bob |
        | --- |
        | cat |
        | cat |

        A video popped into my feed that I liked, about guestbooks: [Veronika Explains \| Guestbook](https://youtu.be/ZSBYO1BYrDM?si=TL2T-jEKnaiFY-sN).
        """).strip()
        self.assertEqual(result, expected)
        self.assertTrue(result.__contains__("\n\n| bob |"))
        self.assertTrue(result.__contains__("| cat |\n\n"))


class TestMarkdownTablesWikilinks(unittest.TestCase):
    """
    Verifies that Obsidian wikilinks inside markdown table cells are correctly
    converted to Jekyll relative note links without breaking table structure.
    """

    def setUp(self):
        self.note_lookup = {
            "First Note": "_posts/2026-09-01-first-note.md",
            "Second Note": "journey/second-note.md",
        }

    def test_wikilinks_in_table_cells_are_converted(self):
        content = dedent("""
        | Topic | Reference |
        | --- | --- |
        | Intro | [[First Note]] |
        | Deep Dive | [[Second Note]] |
        """).strip()

        result = convert_wikilink_note_links_outside_code_blocks_and_code_spans(content, self.note_lookup)

        expected = dedent("""
        | Topic | Reference |
        | --- | --- |
        | Intro | [First Note]({% link _posts/2026-09-01-first-note.md %}) |
        | Deep Dive | [Second Note]({% link journey/second-note.md %}) |
        """).strip()
        self.assertEqual(result, expected)

    def test_wikilinks_with_alias_pipe_in_table_cells_are_converted(self):
        content = dedent("""
        | Topic | Reference |
        | --- | --- |
        | Intro | [[First Note|Read First Note]] |
        | Deep Dive | [[Second Note#Details|Section Details]] |
        """).strip()

        result = convert_wikilink_note_links_outside_code_blocks_and_code_spans(content, self.note_lookup)

        expected = dedent("""
        | Topic | Reference |
        | --- | --- |
        | Intro | [Read First Note]({% link _posts/2026-09-01-first-note.md %}) |
        | Deep Dive | [Section Details]({% link journey/second-note.md %}#details) |
        """).strip()
        self.assertEqual(result, expected)

    def test_inline_code_wikilink_example_in_table_cell_is_untouched(self):
        content = dedent("""
        | Syntax | Example |
        | --- | --- |
        | Note Link | `[[First Note]]` |
        """).strip()

        result = convert_wikilink_note_links_outside_code_blocks_and_code_spans(content, self.note_lookup)

        self.assertEqual(result, content)


class TestMarkdownTablesImages(unittest.TestCase):
    """
    Verifies that wikilink image embeds and markdown images inside table cells
    are converted to single-line inline Jekyll includes, keeping table rows on one line.
    """

    def setUp(self):
        self.image_lookup = {
            "badge.png": "assets/88x31/badge.png",
            "diagram.svg": "assets/posts/diagram.svg",
        }
        self.popup_lookup = {
            "badge.png": {
                "image_source": "https://example.com/badge",
                "popup_blurb": "Cool badge",
                "popup_redirect_text": "Visit Site",
            }
        }

    def test_wikilink_image_embed_in_table_is_converted_to_markdown_image(self):
        content = dedent("""
        | Icon | Description |
        | --- | --- |
        | ![[badge.png]] | Standard badge |
        | ![[diagram.svg|300]] | Architecture |
        """).strip()

        result = convert_wikilink_image_embeds_outside_code_blocks_and_code_spans(content)

        expected = dedent("""
        | Icon | Description |
        | --- | --- |
        | ![badge.png](badge.png) | Standard badge |
        | ![diagram.svg](diagram.svg) | Architecture |
        """).strip()
        self.assertEqual(result, expected)

    def test_markdown_images_in_table_cells_render_as_single_line_inline_includes(self):
        content = dedent("""
        | Preview | Label |
        | --- | --- |
        | ![Badge](badge.png) | Badge 1 |
        | ![Diagram](diagram.svg) | Diagram 1 |
        """).strip()

        result = convert_markdown_image_embeds_outside_code_blocks_and_code_spans(
            content, self.image_lookup, self.popup_lookup
        )

        lines = result.splitlines()
        self.assertEqual(len(lines), 4, "Table should maintain exactly 4 lines (header, separator, 2 rows)")
        self.assertIn('{% include image.html src="assets/88x31/badge.png" alt="Badge"', lines[2])
        self.assertIn('popup_blurb="Cool badge"', lines[2])
        self.assertIn('{% include image.html src="assets/posts/diagram.svg" alt="Diagram"', lines[3])


class TestMarkdownTablesCodeblocksAndCallouts(unittest.TestCase):
    """
    Verifies interaction between markdown tables, fenced code blocks, and callouts.
    """

    def test_table_inside_fenced_code_block_is_raw_escaped(self):
        content = dedent("""
        Here is an example table:
        ```markdown
        | Header A | Header B |
        | --- | --- |
        | 1 | 2 |
        ```
        """).strip()

        result = escape_markdown_code_blocks_for_jekyll(content)

        self.assertIn("{% raw %}\n```markdown\n| Header A | Header B |", result)
        self.assertIn("```\n{% endraw %}", result)


class TestMarkdownTablesFullPipeline(unittest.TestCase):
    """
    End-to-end integration test verifying process_markdown_for_jekyll handles
    complex tables with wikilinks, images, pipes in links, inline code, and callouts.
    """

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)
        self.tmp_path = Path(self.tmp_dir.name)

        self.note_lookup = {
            "Feature Guide": "journey/feature-guide.md",
        }
        self.image_lookup = {
            "preview.png": "assets/posts/preview.png",
        }
        self.popup_lookup = {
            "preview.png": {
                "popup_blurb": "Detailed preview",
            }
        }

    def test_full_markdown_pipeline_on_complex_table(self):
        md_file = self.tmp_path / "table_test.md"
        content = dedent("""
        # Comparison Table

        | Feature | Status | Link | Preview | Code |
        | :--- | :---: | :--- | :---: | ---: |
        | Docs | Active | [[Feature Guide|Guide | Docs]] | ![[preview.png]] | `x | y` |
        | Search | Done | [Docs | Search](https://example.com?q=a|b) | N/A | `foo` |

        > [!tip] Table in Callout
        > | Col A | Col B |
        > | --- | --- |
        > | [[Feature Guide]] | `val | 1` |
        """).strip()

        md_file.write_text(content, encoding="utf-8")

        process_markdown_for_jekyll(md_file, self.note_lookup, self.image_lookup, self.popup_lookup)
        processed = md_file.read_text(encoding="utf-8")

        # 1. Wikilink with alias is converted and its pipe escaped in link text
        self.assertIn(r"[Guide \| Docs]({% link journey/feature-guide.md %})", processed)

        # 2. Markdown link with pipe in text and URL is escaped
        self.assertIn(r"[Docs \| Search](https://example.com?q=a\|b)", processed)

        # 3. Wikilink image embed is converted to inline jekyll image include
        self.assertIn('{% include image.html src="assets/posts/preview.png"', processed)
        self.assertIn('popup_blurb="Detailed preview"', processed)

        # 4. Inline code spans with pipes remain unaltered
        self.assertIn("`x | y`", processed)

        # 5. Callout with table is converted
        self.assertIn('{% include callout.html', processed)
        self.assertIn(r"[Feature Guide]({% link journey/feature-guide.md %})", processed)
        self.assertIn("`val | 1`", processed)


if __name__ == '__main__':
    unittest.main()
