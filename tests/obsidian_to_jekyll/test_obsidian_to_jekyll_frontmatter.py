import tempfile
import unittest
from pathlib import Path

import test_helpers
from test_helpers import register_synced_file
from scripts.parsing_markdown.jekyll_frontmatter import add_frontmatter_to_file


class TestAddFrontmatterToMarkdownFiles(unittest.TestCase):
    """Exercises the orchestration logic — which files get frontmatter injected
    based on changed_dest_paths, name, and extension — not add_frontmatter_to_file itself."""

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)
        self.tmp_path = Path(self.tmp_dir.name)
        self.converter = test_helpers.make_converter(Path(self.tmp_dir.name))
        self.converter.begin_run()
        self.note_lookup = {}
        self.image_lookup = {}

    def test_changed_markdown_file_gets_frontmatter(self):
        dest = self.converter.output_location / "hello-world.md"
        dest.write_text("# Hello", encoding="utf-8")
        register_synced_file(self.converter, dest)

        self.converter.parse_markdown_files_for_jekyll(self.note_lookup, self.image_lookup)

        result = dest.read_text(encoding="utf-8")
        self.assertIn("layout: default", result)
        # title is display_title_from_slug'd (slug -> Title Case), not the raw slug —
        # this assertion previously expected the raw slug, which the code has
        # never actually produced; see TestDisplayTitleFromSlug for that unit directly.
        self.assertIn("title: \"Hello World\"", result)

    def test_about_md_gets_permalink(self):
        dest = self.converter.output_location / "about.md"
        dest.write_text("About me", encoding="utf-8")
        register_synced_file(self.converter, dest)
        self.converter.site_sync.changed_dest_paths = [dest]

        self.converter.parse_markdown_files_for_jekyll(self.note_lookup, self.image_lookup)

        result = dest.read_text(encoding="utf-8")
        self.assertIn("permalink: /about/", result)

    def test_section_file_gets_section_layout_and_frontmatter(self):
        section_dir = self.converter.output_location / "vision" / "design"
        section_dir.mkdir(parents=True)
        dest = section_dir / "website-design.md"
        dest.write_text("Design notes", encoding="utf-8")
        register_synced_file(self.converter, dest)
        self.converter.site_sync.changed_dest_paths = [dest]

        self.converter.parse_markdown_files_for_jekyll(self.note_lookup, self.image_lookup)

        result = dest.read_text(encoding="utf-8")
        self.assertIn("layout: section", result)
        self.assertIn("section: Vision", result)
        self.assertIn("permalink: /vision/design/website-design/", result)

    def test_permalink_omitted_by_default(self):
        md_file = self.tmp_path / "post.md"
        md_file.write_text("Post body", encoding="utf-8")

        add_frontmatter_to_file(md_file)

        result = md_file.read_text(encoding="utf-8")
        self.assertNotIn("permalink:", result)

    def test_custom_layout_is_used(self):
        md_file = self.tmp_path / "post.md"
        md_file.write_text("Body", encoding="utf-8")

        add_frontmatter_to_file(md_file, file_layout="post")

        result = md_file.read_text(encoding="utf-8")
        self.assertIn("layout: post", result)


if __name__ == '__main__':
    unittest.main()
