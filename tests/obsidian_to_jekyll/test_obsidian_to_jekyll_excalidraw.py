import tempfile
import unittest
from pathlib import Path

import test_helpers
from test_helpers import register_synced_file
from scripts.parsing_markdown.wikilinks import build_note_path_lookup


class TestExcalidrawNoteSwap(unittest.TestCase):
    """Covers the orchestration around excalidraw_embeds: swap must happen,
    and must happen BEFORE frontmatter injection so frontmatter survives."""

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)
        self.converter = test_helpers.make_converter(Path(self.tmp_dir.name))
        self.converter.begin_run()
        self.note_lookup = build_note_path_lookup(Path(self.tmp_dir.name))
        self.image_lookup = {}

    def test_excalidraw_note_body_is_swapped_for_image_embed(self):
        dest = self.converter.output_location / "vision-diagram.excalidraw.md"
        dest.write_text('{"type":"excalidraw","elements":[]}', encoding="utf-8")
        register_synced_file(self.converter, dest)
        self.converter.site_sync.changed_dest_paths = [dest]

        self.converter.parse_markdown_files_for_jekyll(self.note_lookup, self.image_lookup)

        result = dest.read_text(encoding="utf-8")
        self.assertNotIn('"type":"excalidraw"', result)
        # swapped content flows through the normal image pipeline, so by the
        # time processing finishes it's a Jekyll image include, not raw markdown
        self.assertIn("{% include figure.html", result)
        self.assertIn('src="vision-diagram.excalidraw.svg"', result)

    def test_excalidraw_note_still_gets_frontmatter(self):
        dest = self.converter.output_location / "vision-diagram.excalidraw.md"
        dest.write_text('{"type":"excalidraw","elements":[]}', encoding="utf-8")
        register_synced_file(self.converter, dest)
        self.converter.site_sync.changed_dest_paths = [dest]

        self.converter.parse_markdown_files_for_jekyll(self.note_lookup, self.image_lookup)

        result = dest.read_text(encoding="utf-8")
        self.assertIn("layout: default", result)

    def test_excalidraw_note_inside_section_still_gets_section_frontmatter(self):
        section_dir = self.converter.output_location / "vision" / "whiteboard"
        section_dir.mkdir(parents=True)
        dest = section_dir / "website-whiteboard.excalidraw.md"
        dest.write_text('{"type":"excalidraw","elements":[]}', encoding="utf-8")
        register_synced_file(self.converter, dest)
        self.converter.site_sync.changed_dest_paths = [dest]

        self.converter.parse_markdown_files_for_jekyll(self.note_lookup, self.image_lookup)

        result = dest.read_text(encoding="utf-8")
        self.assertIn("layout: section", result)
        self.assertIn("section: Vision", result)
        self.assertIn('src="website-whiteboard.excalidraw.svg"', result)

    def test_non_excalidraw_markdown_file_is_unaffected(self):
        dest = self.converter.output_location / "about.md"
        dest.write_text("About me", encoding="utf-8")
        register_synced_file(self.converter, dest)
        self.converter.site_sync.changed_dest_paths = [dest]

        self.converter.parse_markdown_files_for_jekyll(self.note_lookup, self.image_lookup)

        result = dest.read_text(encoding="utf-8")
        self.assertIn("About me", result)
        self.assertNotIn("{% include image.html", result)


if __name__ == '__main__':
    unittest.main()
