import tempfile
import unittest
from pathlib import Path

import test_helpers
from test_helpers import register_synced_file
from scripts.parsing_markdown.wikilinks import build_note_path_lookup


class TestMarkdownFileConversion(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)
        self.converter = test_helpers.make_converter(Path(self.tmp_dir.name))
        self.converter.begin_run()
        self.note_lookup = build_note_path_lookup(Path(self.tmp_dir.name))
        self.image_lookup = {}

    def test_ignored_files_are_skipped(self):
        for name in self.converter.IGNORED_FRONTMATTER_FILES:
            dest = self.converter.output_location / name
            dest.write_text("original content", encoding="utf-8")
            register_synced_file(self.converter, dest)
            self.converter.site_sync.changed_dest_paths = [dest]

            self.converter.parse_markdown_files_for_jekyll(self.note_lookup, self.image_lookup)

            self.assertEqual(dest.read_text(encoding="utf-8"), "original content")

    def test_non_markdown_files_are_skipped(self):
        dest = self.converter.output_location / "style.css"
        dest.write_text("body {}", encoding="utf-8")
        self.converter.site_sync.changed_dest_paths = [dest]

        self.converter.parse_markdown_files_for_jekyll(self.note_lookup, self.image_lookup)

        self.assertEqual(dest.read_text(encoding="utf-8"), "body {}")

    def test_cache_hit_file_not_in_changed_dest_paths_is_untouched(self):
        # simulates a recurring run where this file was a cache hit (unchanged) —
        # it should NOT reappear in changed_dest_paths, and must not get double-frontmatter
        dest = self.converter.output_location / "post.md"
        original = "---\nlayout: default\ntitle: post\n---\n\nBody"
        dest.write_text(original, encoding="utf-8")
        self.converter.site_sync.changed_dest_paths = []  # nothing changed this run

        self.converter.parse_markdown_files_for_jekyll(self.note_lookup, self.image_lookup)

        self.assertEqual(dest.read_text(encoding="utf-8"), original)

    def test_multiple_changed_files_all_get_processed(self):
        dest_a = self.converter.output_location / "post-a.md"
        dest_b = self.converter.output_location / "post-b.md"
        dest_a.write_text("A", encoding="utf-8")
        dest_b.write_text("B", encoding="utf-8")
        register_synced_file(self.converter, dest_a)
        register_synced_file(self.converter, dest_b)
        self.converter.site_sync.changed_dest_paths = [dest_a, dest_b]

        self.converter.parse_markdown_files_for_jekyll(self.note_lookup, self.image_lookup)

        # title is display_title_from_slug'd (slug -> Title Case) — see note above.
        self.assertIn("title: \"Post A\"", dest_a.read_text(encoding="utf-8"))
        self.assertIn("title: \"Post B\"", dest_b.read_text(encoding="utf-8"))


if __name__ == '__main__':
    unittest.main()
