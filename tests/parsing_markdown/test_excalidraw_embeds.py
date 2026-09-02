import tempfile
import unittest
from pathlib import Path

from scripts.parsing_markdown.excalidraw_embeds import (
    is_excalidraw_note,
    excalidraw_svg_filename,
    swap_excalidraw_note_with_image_embed,
)


class TestIsExcalidrawNote(unittest.TestCase):

    def test_excalidraw_note_is_detected(self):
        self.assertTrue(is_excalidraw_note(Path("journey-diagram.excalidraw.md")))

    def test_regular_note_is_not_detected(self):
        self.assertFalse(is_excalidraw_note(Path("about.md")))

    def test_note_with_excalidraw_elsewhere_in_name_is_not_detected(self):
        # only the exact `.excalidraw.md` suffix counts — a coincidental
        # substring earlier in the name shouldn't trigger a swap
        self.assertFalse(is_excalidraw_note(Path("my-excalidraw-notes.md")))


class TestExcalidrawSvgFilename(unittest.TestCase):

    def test_md_suffix_swapped_for_svg(self):
        result = excalidraw_svg_filename(Path("journey-diagram.excalidraw.md"))
        self.assertEqual(result, "journey-diagram.excalidraw.svg")

    def test_preserves_folder_agnostic_basename_only(self):
        result = excalidraw_svg_filename(Path("journey/whiteboard/website-whiteboard.excalidraw.md"))
        self.assertEqual(result, "website-whiteboard.excalidraw.svg")


class TestSwapExcalidrawNoteWithImageEmbed(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)
        self.tmp_path = Path(self.tmp_dir.name)

    def test_entire_file_content_is_replaced_with_image_markdown(self):
        note = self.tmp_path / "journey-diagram.excalidraw.md"
        note.write_text('---\nexcalidraw-plugin: parsed\n---\n{"type":"excalidraw","elements":[...]}', encoding="utf-8")

        swap_excalidraw_note_with_image_embed(note)

        result = note.read_text(encoding="utf-8")
        self.assertEqual(result, "![journey-diagram.excalidraw.svg](journey-diagram.excalidraw.svg)\n")

    def test_no_leftover_scene_data_or_frontmatter(self):
        note = self.tmp_path / "drawing.excalidraw.md"
        note.write_text('{"type":"excalidraw","source":"https://excalidraw.com"}', encoding="utf-8")

        swap_excalidraw_note_with_image_embed(note)

        result = note.read_text(encoding="utf-8")
        self.assertNotIn("excalidraw-plugin", result)
        self.assertNotIn('"type":"excalidraw"', result)


if __name__ == '__main__':
    unittest.main()
