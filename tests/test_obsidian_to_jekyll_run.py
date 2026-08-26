import tempfile
import unittest
from pathlib import Path

from scripts.obsidian_to_jekyll import ObsidianToJekyllConverter, MANIFEST_FILENAME


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

        hello = (self.output / "_posts" / "hello.md").read_text(encoding="utf-8")
        self.assertIn("{% link about/about.md %}", hello)

        self.assertTrue((self.output / "assets" / "images" / "photo.png").exists())
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

    def test_missing_vault_does_not_raise_and_produces_no_output(self):
        missing_vault = self.tmp_path / "does-not-exist"
        converter = ObsidianToJekyllConverter(missing_vault, self.output, self.source)

        converter.run()  # should print a message and return, not raise

        self.assertFalse(self.output.exists())


if __name__ == '__main__':
    unittest.main()
