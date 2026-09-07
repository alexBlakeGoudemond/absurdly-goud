import unittest
from textwrap import dedent

from scripts.parsing_markdown.callouts import (
    DEFAULT_TITLES,
    TYPE_ALIASES,
    CalloutBlock,
    convert_obsidian_callouts_to_jekyll_includes,
    parse_callout_block,
    render_callout_as_jekyll_include,
)

# One markdown fixture per Obsidian callout keyword (canonical type AND every
# alias), each with a nested_content string standing in for what the body
# would look like AFTER wikilinks.py / markdown_images.py have already run
# (see callouts.py's module docstring on pipeline ordering) -- i.e. plain
# markdown/Liquid, never raw [[wikilink]] or ![[embed]] syntax.
CALLOUT_KEYWORD_TEST_CASES = [
    # (keyword as typed in source, expected canonical type)
    ("note", "note"),
    ("abstract", "abstract"),
    ("summary", "abstract"),
    ("tldr", "abstract"),
    ("info", "info"),
    ("todo", "todo"),
    ("important", "important"),
    ("tip", "important"),
    ("hint", "important"),
    ("success", "success"),
    ("check", "success"),
    ("done", "success"),
    ("question", "question"),
    ("help", "question"),
    ("faq", "question"),
    ("warning", "warning"),
    ("caution", "warning"),
    ("attention", "warning"),
    ("failure", "failure"),
    ("fail", "failure"),
    ("missing", "failure"),
    ("danger", "danger"),
    ("error", "danger"),
    ("bug", "bug"),
    ("example", "example"),
    ("quote", "quote"),
    ("cite", "quote"),
]


class TestCalloutKeywordsResolveToCanonicalType(unittest.TestCase):
    """Data-driven: every keyword Obsidian recognizes (13 types + all their
    aliases) must resolve to the right canonical type and its default title,
    both directly via parse_callout_block and end-to-end via the top-level
    convert function."""

    def test_every_known_keyword_resolves_to_its_canonical_type_and_default_title(self):
        for keyword, expected_canonical in CALLOUT_KEYWORD_TEST_CASES:
            with self.subTest(keyword=keyword):
                lines = [f'> [!{keyword}]', '> Some content']

                callout = parse_callout_block(lines)

                self.assertEqual(callout.canonical_type, expected_canonical)
                self.assertEqual(callout.title, DEFAULT_TITLES[expected_canonical])
                self.assertEqual(callout.content, 'Some content')

    def test_every_known_keyword_is_case_insensitive(self):
        for keyword, expected_canonical in CALLOUT_KEYWORD_TEST_CASES:
            with self.subTest(keyword=keyword):
                lines = [f'> [!{keyword.upper()}]', '> Some content']

                callout = parse_callout_block(lines)

                self.assertEqual(callout.canonical_type, expected_canonical)

    def test_type_aliases_table_matches_default_titles_table(self):
        # Guards against the two tables drifting apart as types are added.
        self.assertEqual(set(TYPE_ALIASES.values()), set(DEFAULT_TITLES.keys()))


class TestParseCalloutBlock(unittest.TestCase):

    def test_plain_blockquote_without_header_returns_none(self):
        lines = ['> Just a regular quote', '> with two lines']

        self.assertIsNone(parse_callout_block(lines))

    def test_custom_title_overrides_default_title(self):
        lines = ['> [!note] My Custom Title', '> Body text']

        callout = parse_callout_block(lines)

        self.assertEqual(callout.title, 'My Custom Title')

    def test_unknown_type_falls_back_to_note_and_keeps_typed_word_as_title(self):
        # Mirrors Obsidian's own behaviour: an unrecognized type still
        # renders (as "note" styling) rather than being left unstyled,
        # and shows the author's original word rather than "Note".
        lines = ['> [!nonexistent-type]', '> Body text']

        callout = parse_callout_block(lines)

        self.assertEqual(callout.canonical_type, 'note')
        self.assertEqual(callout.title, 'nonexistent-type')

    def test_unknown_type_with_custom_title_uses_custom_title_not_typed_word(self):
        lines = ['> [!nonexistent-type] Real Title', '> Body text']

        callout = parse_callout_block(lines)

        self.assertEqual(callout.canonical_type, 'note')
        self.assertEqual(callout.title, 'Real Title')

    def test_no_fold_marker_is_not_collapsible(self):
        lines = ['> [!note]', '> Body text']

        callout = parse_callout_block(lines)
        self.assertFalse(callout.collapsible)
        self.assertFalse(callout.initially_collapsed)

    def test_minus_fold_marker_is_collapsible_and_starts_collapsed(self):
        lines = ['> [!note]-', '> Body text']

        callout = parse_callout_block(lines)
        self.assertTrue(callout.collapsible)
        self.assertTrue(callout.initially_collapsed)

    def test_plus_fold_marker_is_collapsible_and_starts_expanded(self):
        lines = ['> [!note]+', '> Body text']

        callout = parse_callout_block(lines)
        self.assertTrue(callout.collapsible)
        self.assertFalse(callout.initially_collapsed)

    def test_fold_marker_alongside_custom_title(self):
        lines = ['> [!tip]- Collapsed Tip', '> Body text']

        callout = parse_callout_block(lines)

        self.assertTrue(callout.collapsible)
        self.assertTrue(callout.initially_collapsed)
        self.assertEqual(callout.title, 'Collapsed Tip')

    def test_header_with_no_space_before_bracket_is_still_recognized(self):
        lines = ['>[!note]', '>Body text']

        callout = parse_callout_block(lines)

        self.assertEqual(callout.canonical_type, 'note')
        self.assertEqual(callout.content, 'Body text')

    def test_callout_with_no_body_content(self):
        lines = ['> [!note] Title only, no body']

        callout = parse_callout_block(lines)

        self.assertEqual(callout.title, 'Title only, no body')
        self.assertEqual(callout.content, '')

    def test_multiline_content_with_blank_quoted_line_preserves_paragraph_break(self):
        # A bare `>` line inside a callout is a blockquote continuation line
        # (paragraph break WITHIN the callout), not the end of the blockquote
        # -- it must be preserved as a real blank line in extracted content,
        # not dropped, so markdownify can still see two separate paragraphs.
        lines = ['> [!note]', '> First paragraph.', '>', '> Second paragraph.']

        callout = parse_callout_block(lines)

        self.assertEqual(callout.content, 'First paragraph.\n\nSecond paragraph.')

    def test_wikilink_already_resolved_to_jekyll_link_passes_through_unchanged(self):
        # By the time callouts.py runs, wikilinks.py has already turned
        # [[Note]] into [Note]({% link Note.md %}) -- this module must not
        # re-touch it.
        lines = ['> [!note]', '> See [2026-09-03 Ducks]({% link 2026-09-03-ducks.md %}) for more.']

        callout = parse_callout_block(lines)

        self.assertEqual(callout.content, 'See [2026-09-03 Ducks]({% link 2026-09-03-ducks.md %}) for more.')

    def test_image_already_resolved_to_jekyll_include_passes_through_unchanged(self):
        # By the time callouts.py runs, markdown_images.py has already turned
        # ![[image.gif]] into a {% include image.html %} tag.
        lines = ['> [!note]', '> Inline: {% include image.html src="free-real-estate.gif" alt="" title="" %}']

        callout = parse_callout_block(lines)

        self.assertIn('{% include image.html src="free-real-estate.gif"', callout.content)

    def test_table_lines_pass_through_unchanged(self):
        # Whether this renders as a real <table> depends on kramdown getting
        # blank `>` lines around it inside the blockquote -- a known,
        # separate issue (see project notes) unrelated to extraction here.
        # This test only locks down that callouts.py doesn't mangle the
        # pipe-table text itself.
        lines = [
            '> [!note]',
            '> | Heading 1 | Heading 2 |',
            '> |---|---|',
            '> | Content 1 | Content 2 |',
        ]

        callout = parse_callout_block(lines)

        self.assertEqual(
            callout.content,
            '| Heading 1 | Heading 2 |\n|---|---|\n| Content 1 | Content 2 |',
        )


class TestRenderCalloutAsJekyllInclude(unittest.TestCase):

    def test_renders_capture_and_include_tags_with_expected_contract(self):
        callout = CalloutBlock(canonical_type='note', title='Note', collapsible=False, content='Body text')

        result = render_callout_as_jekyll_include(callout, index=0)

        self.assertEqual(
            result,
            dedent('''\
                {% capture callout_content_0 %}
                Body text
                {% endcapture %}
                {% include callout.html type="note" title="Note" collapsible=false content=callout_content_0 %}'''),
        )

    def test_collapsible_true_renders_as_liquid_true(self):
        callout = CalloutBlock(canonical_type='tip', title='Tip', collapsible=True, content='x')

        result = render_callout_as_jekyll_include(callout, index=0)

        self.assertIn('collapsible=true', result)
        self.assertIn('initially_collapsed=false', result)

    def test_collapsible_and_initially_collapsed_renders_state(self):
        callout = CalloutBlock(canonical_type='tip', title='Tip', collapsible=True, content='x', initially_collapsed=True)

        result = render_callout_as_jekyll_include(callout, index=0)

        self.assertIn('initially_collapsed=true', result)

    def test_index_disambiguates_capture_variable_name(self):
        callout = CalloutBlock(canonical_type='note', title='Note', collapsible=False, content='x')

        result = render_callout_as_jekyll_include(callout, index=7)

        self.assertIn('{% capture callout_content_7 %}', result)
        self.assertIn('content=callout_content_7', result)

    def test_title_containing_double_quote_is_wrapped_in_single_quotes(self):
        callout = CalloutBlock(canonical_type='note', title='He said "hi"', collapsible=False, content='x')

        result = render_callout_as_jekyll_include(callout, index=0)

        self.assertIn("title='He said \"hi\"'", result)


class TestConvertObsidianCalloutsToJekyllIncludes(unittest.TestCase):

    def test_file_with_no_callouts_is_unchanged(self):
        content = dedent('''\
            # A heading

            Just a normal paragraph, no callouts here.
            ''')

        result = convert_obsidian_callouts_to_jekyll_includes(content)

        self.assertEqual(result, content)

    def test_plain_blockquote_without_callout_header_is_left_untouched(self):
        content = dedent('''\
            > Just a regular quote
            > with two lines
            ''')

        result = convert_obsidian_callouts_to_jekyll_includes(content)

        self.assertEqual(result, content)
        self.assertNotIn('{% include callout.html', result)

    def test_simple_note_callout_is_converted(self):
        content = dedent('''\
            Some text before.

            > [!note]
            > This has a 'note' Style

            Some text after.
            ''')

        result = convert_obsidian_callouts_to_jekyll_includes(content)

        self.assertIn('Some text before.', result)
        self.assertIn('Some text after.', result)
        self.assertIn('{% capture callout_content_0 %}', result)
        self.assertIn("This has a 'note' Style", result)
        self.assertIn('{% include callout.html type="note" title="Note" collapsible=false content=callout_content_0 %}', result)
        self.assertNotIn('[!note]', result)

    def test_callout_with_wikilink_already_resolved(self):
        content = dedent('''\
            > [!note]
            > This has a wikilink to another note: [2026-09-03 Ducks]({% link 2026-09-03-ducks.md %})
            ''')

        result = convert_obsidian_callouts_to_jekyll_includes(content)

        self.assertIn('[2026-09-03 Ducks]({% link 2026-09-03-ducks.md %})', result)

    def test_callout_with_inline_image_already_resolved(self):
        content = dedent('''\
            > [!note]
            > This has an embedded image: {% include image.html src="free-real-estate.gif" alt="" title="" %}
            ''')

        result = convert_obsidian_callouts_to_jekyll_includes(content)

        self.assertIn('{% include image.html src="free-real-estate.gif" alt="" title="" %}', result)

    def test_callout_header_inside_fenced_code_block_is_not_converted(self):
        content = dedent('''\
            Here is an example of the syntax:

            ```markdown
            > [!note]
            > This has a 'note' Style
            ```
            ''')

        result = convert_obsidian_callouts_to_jekyll_includes(content)

        self.assertIn('> [!note]', result)
        self.assertNotIn('{% include callout.html', result)

    def test_multiple_callouts_in_one_file_get_unique_capture_variable_names(self):
        content = dedent('''\
            > [!note]
            > First callout.

            > [!warning]
            > Second callout.
            ''')

        result = convert_obsidian_callouts_to_jekyll_includes(content)

        self.assertIn('{% capture callout_content_0 %}', result)
        self.assertIn('content=callout_content_0', result)
        self.assertIn('{% capture callout_content_1 %}', result)
        self.assertIn('content=callout_content_1', result)
        self.assertIn('type="note"', result)
        self.assertIn('type="warning"', result)

    def test_callout_and_plain_blockquote_in_the_same_file(self):
        content = dedent('''\
            > A plain quote, not a callout.

            > [!info]
            > A real callout.
            ''')

        result = convert_obsidian_callouts_to_jekyll_includes(content)

        self.assertIn('> A plain quote, not a callout.', result)
        self.assertIn('{% include callout.html type="info"', result)

    def test_callout_containing_a_table(self):
        content = dedent('''\
            > [!note]
            > | Heading 1 | Heading 2 |
            > |---|---|
            > | Content 1 | Content 2 |
            ''')

        result = convert_obsidian_callouts_to_jekyll_includes(content)

        self.assertIn('{% capture callout_content_0 %}', result)
        self.assertIn('| Heading 1 | Heading 2 |', result)
        self.assertIn('|---|---|', result)
        self.assertIn('| Content 1 | Content 2 |', result)

    def test_real_world_fixture_with_multiple_callout_flavours(self):
        # Mirrors the actual test note used to validate the site
        # (2026-09-06 Blockquotes and Markdown Notation.md), post
        # wikilink/image resolution.
        content = dedent('''\
            Obsidian has callouts notation. Below are examples.

            > [!note]
            > This has a 'note' Style

            > [!note]
            > This has a wikilink to another note: [2026-09-03 Ducks]({% link 2026-09-03-ducks.md %})

            > [!note]
            > This has an embedded image (should show as inline image): {% include image.html src="free-real-estate.gif" alt="" title="" %}

            >[!Note]
            >This has a image on its own line (should show as figure):
            >{% include figure.html src="this-is-fine-fire.gif" alt="" title="" %}
            ''')

        result = convert_obsidian_callouts_to_jekyll_includes(content)

        self.assertEqual(result.count('{% include callout.html'), 4)
        self.assertEqual(result.count('type="note"'), 4)
        for index in range(4):
            self.assertIn(f'callout_content_{index}', result)
        self.assertNotIn('[!Note]', result)
        self.assertNotIn('[!note]', result)


if __name__ == '__main__':
    unittest.main()