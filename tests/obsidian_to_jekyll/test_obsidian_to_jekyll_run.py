import tempfile
import unittest
from pathlib import Path

from scripts.obsidian_to_jekyll import (
    ObsidianToJekyllConverter,
    MANIFEST_FILENAME,
)


class TestRunEndToEnd(unittest.TestCase):
    """No test previously drove run() itself end-to-end — every other test
    exercises the converter's sub-methods directly. This covers the full
    pipeline against a small fake vault: copying, image collection,
    frontmatter injection, wikilink/image conversion, and manifest writing,
    all wired together the way the real entrypoint invokes them."""

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)
        self.tmp_path = Path(self.tmp_dir.name)
        self.vault = self.tmp_path / "vault"
        self.output = self.tmp_path / "output"
        self.source = self.tmp_path / "source"
        self.vault.mkdir()
        self.source.mkdir()
        # output dir intentionally NOT pre-created — run() should create it

    def test_run_produces_expected_output_tree(self):
        about_dir = self.vault / "about"
        about_dir.mkdir()
        (about_dir / "about.md").write_text("About me\n\n![Photo](photo.png)", encoding="utf-8")
        (self.vault / "photo.png").write_bytes(b"fake-bytes")
        posts_dir = self.vault / "posts"
        posts_dir.mkdir()
        (posts_dir / "hello.md").write_text("# Hello\n\n[[about]]", encoding="utf-8")
        (self.source / "CNAME").write_text("example.com", encoding="utf-8")

        converter = ObsidianToJekyllConverter(self.vault, self.output, self.source)
        converter.run()

        about = (self.output / "about" / "about.md").read_text(encoding="utf-8")
        self.assertIn("permalink: /about/", about)
        self.assertIn("{% include image.html", about)
        # photo.png sits at the vault root (no parent dir), so it lands
        # directly under assets/ with no bucket, and the resolved src
        # reflects that.
        self.assertIn('src="assets/photo.png"', about)

        hello = (self.output / "_posts" / "hello.md").read_text(encoding="utf-8")
        self.assertIn("{% link about/about.md %}", hello)

        self.assertTrue((self.output / "assets" / "photo.png").exists())
        self.assertTrue((self.output / "CNAME").exists())
        self.assertTrue((self.output / MANIFEST_FILENAME).exists())

    def test_second_run_with_no_changes_touches_nothing_new(self):
        about_dir = self.vault / "about"
        about_dir.mkdir()
        (about_dir / "about.md").write_text("About me", encoding="utf-8")

        first_converter = ObsidianToJekyllConverter(self.vault, self.output, self.source)
        first_converter.run()
        first_output = (self.output / "about" / "about.md").read_text(encoding="utf-8")

        second_converter = ObsidianToJekyllConverter(self.vault, self.output, self.source)
        second_converter.run()
        second_output = (self.output / "about" / "about.md").read_text(encoding="utf-8")

        self.assertEqual(first_output, second_output)

    def test_excalidraw_note_ends_up_as_a_working_image_include(self):
        whiteboard_dir = self.vault / "vision" / "whiteboard"
        whiteboard_dir.mkdir(parents=True)
        (whiteboard_dir / "website-whiteboard.excalidraw.md").write_text(
            '{"type":"excalidraw","elements":[]}', encoding="utf-8"
        )
        #!important SVG is expected to exist due to Obsidian settings "Auto export svg" setting - simulate
        (whiteboard_dir / "website-whiteboard.excalidraw.svg").write_text(
            "<svg></svg>", encoding="utf-8"
        )

        converter = ObsidianToJekyllConverter(self.vault, self.output, self.source)
        converter.run()

        note = (self.output / "vision" / "whiteboard" / "website-whiteboard.excalidraw.md").read_text(encoding="utf-8")
        self.assertNotIn('"type":"excalidraw"', note)
        self.assertIn("{% include image.html", note)
        # The SVG lives under vault/vision/whiteboard/, so it's bucketed
        # into assets/vision/, and the resolved src reflects that bucket.
        self.assertIn('src="assets/vision/website-whiteboard.excalidraw.svg"', note)
        self.assertIn("layout: section", note)

        self.assertTrue(
            (self.output / "assets" / "vision" / "website-whiteboard.excalidraw.svg").exists()
        )

    def test_replacing_excalidraw_note_does_not_create_svg(self):
        whiteboard_dir = self.vault / "vision" / "whiteboard"
        whiteboard_dir.mkdir(parents=True)
        (whiteboard_dir / "website-whiteboard.excalidraw.md").write_text(
            '{"type":"excalidraw","elements":[]}', encoding="utf-8"
        )

        converter = ObsidianToJekyllConverter(self.vault, self.output, self.source)
        converter.run()

        note = (self.output / "vision" / "whiteboard" / "website-whiteboard.excalidraw.md").read_text(encoding="utf-8")
        self.assertNotIn('"type":"excalidraw"', note)
        self.assertIn("{% include image.html", note)
        self.assertIn('src="website-whiteboard.excalidraw.svg"', note)
        self.assertIn("layout: section", note)

        self.assertFalse(
            (self.output / "assets" / "vision" / "website-whiteboard.excalidraw.svg").exists()
        )

    def test_image_in_non_posts_folder_is_not_duplicated(self):
        # Regression test: images used to be copied twice for any vault
        # folder other than posts/ — once verbatim by copy_vault_resources,
        # once bucketed into assets/ by copy_vault_images_into_assets_directory.
        buttons_dir = self.vault / "88x31" / "memes-as-buttons"
        buttons_dir.mkdir(parents=True)
        (buttons_dir / "free-real-estate.svg").write_text("<svg></svg>", encoding="utf-8")

        converter = ObsidianToJekyllConverter(self.vault, self.output, self.source)
        converter.run()

        self.assertTrue(
            (self.output / "assets" / "88x31" / "free-real-estate.svg").exists()
        )
        self.assertFalse(
            (self.output / "88x31" / "memes-as-buttons" / "free-real-estate.svg").exists()
        )
        self.assertFalse((self.output / "88x31").exists())

    def test_missing_vault_does_not_raise_and_produces_no_output(self):
        missing_vault = self.tmp_path / "does-not-exist"
        converter = ObsidianToJekyllConverter(missing_vault, self.output, self.source)

        converter.run()  # should print a message and return, not raise

        self.assertFalse(self.output.exists())


if __name__ == '__main__':
    unittest.main()
