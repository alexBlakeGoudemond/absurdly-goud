import tempfile
import unittest
from pathlib import Path
from textwrap import dedent

from scripts.parsing_markdown.image_popups import (
    DEFAULT_POPUP_BLURB,
    load_image_popup_entries,
)

from scripts.parsing_markdown.markdown_images import (
    convert_markdown_image_notation_to_jekyll_includes_image_notation,
)


class TestFigureHasNoPopupBehaviour(unittest.TestCase):
    """Bullet 1: a standalone image (is_inline=False) renders as a figure
    include and never carries popup attributes — even if popup_source /
    popup_blurb are passed in, since a figure isn't the thing that opens
    a popup."""

    def test_figure_include_has_no_popup_attributes(self):
        actual_syntax = convert_markdown_image_notation_to_jekyll_includes_image_notation(
            'image.png', 'Alt text', is_inline=False,
            popup_source='https://example.com', popup_blurb='A cool button',
        )

        self.assertNotIn('popup_src', actual_syntax)
        self.assertNotIn('popup_blurb', actual_syntax)
        self.assertIn('{% include figure.html', actual_syntax)


class TestInlineImageHasPopupBehaviour(unittest.TestCase):
    """Bullet 2: an inline image (is_inline=True) always carries popup
    attributes — with or without a YAML entry behind it."""

    def test_inline_image_include_has_popup_attributes(self):
        actual_syntax = convert_markdown_image_notation_to_jekyll_includes_image_notation(
            'image.png', 'Alt text', is_inline=True,
        )

        self.assertIn('popup_src=', actual_syntax)
        self.assertIn('popup_blurb=', actual_syntax)
        self.assertIn('{% include image.html', actual_syntax)


class TestInlineImageWithYamlEntry(unittest.TestCase):
    """Bullet 3: when a YAML entry exists, the popup uses its image_source
    (local vault path or external URL, either way just dropped straight
    into popup_src) and its blurb — not the fallback."""

    def test_inline_image_with_entry_uses_yaml_source_and_blurb(self):
        actual_syntax = convert_markdown_image_notation_to_jekyll_includes_image_notation(
            'free-real-estate.gif', 'Free real estate',
            is_inline=True,
            popup_source='https://knowyourmeme.com/memes/free-real-estate',
            popup_blurb='A classic meme',
        )

        self.assertIn('popup_src="https://knowyourmeme.com/memes/free-real-estate"', actual_syntax)
        self.assertIn('popup_blurb="A classic meme"', actual_syntax)

    def test_yaml_blurb_is_not_overridden_by_default(self):
        actual_syntax = convert_markdown_image_notation_to_jekyll_includes_image_notation(
            'free-real-estate.gif', 'Free real estate',
            is_inline=True,
            popup_source='https://knowyourmeme.com/memes/free-real-estate',
            popup_blurb='A classic meme',
        )

        self.assertNotIn(DEFAULT_POPUP_BLURB, actual_syntax)


class TestInlineImageWithoutYamlEntry(unittest.TestCase):
    """Bullet 4: with no YAML entry, the popup still shows the original
    image plus a fallback blurb, and 'tell me more' self-links to the
    image's own (already-resolved) path."""

    def test_inline_image_without_entry_falls_back_to_self_link_and_default_blurb(self):
        actual_syntax = convert_markdown_image_notation_to_jekyll_includes_image_notation(
            'assets/88x31/buttons-memes/this-is-fine-fire.gif', 'This is fine',
            is_inline=True,
            popup_source=None, popup_blurb=None,
        )

        self.assertIn(
            'popup_src="assets/88x31/buttons-memes/this-is-fine-fire.gif"', actual_syntax
        )
        self.assertIn(f'popup_blurb="{DEFAULT_POPUP_BLURB}"', actual_syntax)


class TestLoadImagePopupEntries(unittest.TestCase):
    """Mirrors website_manifest.load_manifest's tolerance: missing or
    corrupt data files never crash the build, they just yield no entries."""

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)
        self.data_path = Path(self.tmp_dir.name) / 'image_popups.yml'

    def test_entries_are_keyed_by_image_filename(self):
        self.data_path.write_text(dedent("""\
            - image_vault: "assets/88x31/buttons-memes/free-real-estate.gif"
              image_source: "https://knowyourmeme.com/memes/free-real-estate"
              popup_blurb: "A classic meme"
            """), encoding='utf-8')

        entries = load_image_popup_entries(self.data_path)

        self.assertEqual(
            entries['free-real-estate.gif'],
            {
                'image_source': 'https://knowyourmeme.com/memes/free-real-estate',
                'popup_blurb': 'A classic meme',
            },
        )

    def test_local_vault_source_is_preserved_as_is(self):
        # A local vault path is stored verbatim here — resolving it to a
        # real output path is the converter's job (same lookup used for
        # image_vault), not the YAML loader's.
        self.data_path.write_text(dedent("""\
            - image_vault: "assets/88x31/buttons-memes/good-news-everyone.gif"
              image_source: "assets/source/88x31/buttons-memes/good-news-everyone.gif"
              popup_blurb: "Good news, everyone!"
            """), encoding='utf-8')

        entries = load_image_popup_entries(self.data_path)

        self.assertEqual(
            entries['good-news-everyone.gif']['image_source'],
            'assets/source/88x31/buttons-memes/good-news-everyone.gif',
        )

    def test_missing_file_returns_empty_dict(self):
        entries = load_image_popup_entries(self.data_path)

        self.assertEqual(entries, {})

    def test_corrupt_yaml_returns_empty_dict_instead_of_raising(self):
        self.data_path.write_text("- image_vault: [unclosed", encoding='utf-8')

        entries = load_image_popup_entries(self.data_path)

        self.assertEqual(entries, {})

    def test_empty_file_returns_empty_dict(self):
        self.data_path.write_text("", encoding='utf-8')

        entries = load_image_popup_entries(self.data_path)

        self.assertEqual(entries, {})


if __name__ == '__main__':
    unittest.main()
