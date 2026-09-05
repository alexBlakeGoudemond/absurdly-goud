import tempfile
import unittest
from pathlib import Path

from scripts.parsing_markdown.jekyll_frontmatter import (
    extract_title_from_file_name,
    display_title_from_slug,
    build_permalink,
    strip_existing_frontmatter,
    add_frontmatter_to_file,
    extract_creation_date_from_file_name,
)


class TestExtractTitleFromFileName(unittest.TestCase):

    def test_strips_date_prefix_and_extension(self):
        title = extract_title_from_file_name("2026-08-19-hello-world.md")
        self.assertEqual(title, "hello-world")

    def test_no_date_prefix_still_strips_extension(self):
        title = extract_title_from_file_name("about.md")
        self.assertEqual(title, "about")

    def test_non_md_extension_is_untouched(self):
        title = extract_title_from_file_name("home.mdx")
        self.assertEqual(title, "home.mdx")


class TestExtractCreationDateFromFileName(unittest.TestCase):

    def test_strips_file_title_and_extension(self):
        title = extract_creation_date_from_file_name("2026-08-19-hello-world.md")
        self.assertEqual(title, "2026-08-19")

    def test_no_creation_date_in_final_name_returns_nothing(self):
        title = extract_creation_date_from_file_name("hello-world.md")
        self.assertEqual(title, "")

class TestDisplayTitleFromSlug(unittest.TestCase):

    def test_hyphens_become_spaces_and_title_case(self):
        self.assertEqual(display_title_from_slug("website-inspiration"), "Website Inspiration")
        self.assertEqual(display_title_from_slug("my-cool-note"), "My Cool Note")


class TestBuildPermalink(unittest.TestCase):

    def test_no_section_uses_flat_title_permalink(self):
        permalink = build_permalink(Path("about.md"), "about", section=None)
        self.assertEqual(permalink, "/about/")

    def test_section_file_gets_nested_permalink(self):
        markdown_file = Path("journey/design/website-inspiration.md")

        permalink = build_permalink(markdown_file, "website-inspiration", section="journey")

        self.assertEqual(permalink, "/journey/design/website-inspiration/")

    def test_section_index_page_does_not_stutter_folder_name(self):
        # website-design.md living in a folder called design/ is that folder's
        # index page — /journey/design/, not /journey/design/design/.
        markdown_file = Path("journey/design/design.md")

        permalink = build_permalink(markdown_file, "design", section="journey")

        self.assertEqual(permalink, "/journey/design/")

    def test_file_not_under_section_folder_raises_value_error(self):
        # The file lives under 'journey/', but the caller asked for a
        # permalink relative to a 'blog/' section it never appears in.
        markdown_file = Path("journey/design/website-inspiration.md")

        with self.assertRaises(ValueError) as raised:
            build_permalink(markdown_file, "website-inspiration", section="blog")

        message = str(raised.exception)
        self.assertIn(str(markdown_file), message)
        self.assertIn("blog/", message)

    def test_section_match_is_case_insensitive(self):
        # section folder on disk is lowercase; the section name passed in
        # is not — this still needs to resolve rather than raising.
        markdown_file = Path("journey/Design/website-inspiration.md")

        permalink = build_permalink(markdown_file, "website-inspiration", section="journey")

        self.assertEqual(permalink, "/journey/design/website-inspiration/")

    def test_section_file_nested_five_levels_deep_preserves_full_path(self):
        # A note nested multiple folders deep under the section root should
        # produce a permalink containing every intermediate folder, not just
        # the immediate parent — e.g. a file five levels under journey/ should
        # not collapse its URL down to a single subfolder segment.
        markdown_file = Path("journey/design/mockups/homepage/desktop/hero-section.md")

        permalink = build_permalink(markdown_file, "hero-section", section="journey")

        self.assertEqual(permalink, "/journey/design/mockups/homepage/desktop/hero-section/")


class TestStripExistingFrontmatter(unittest.TestCase):

    def test_removes_leading_frontmatter_block(self):
        content = "---\nfoo: bar\n---\nBody text"

        result = strip_existing_frontmatter(content)

        self.assertEqual(result, "Body text")

    def test_content_without_frontmatter_is_unchanged(self):
        content = "Just body text"

        result = strip_existing_frontmatter(content)

        self.assertEqual(result, content)


class TestAddFrontmatterToFile(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)
        self.tmp_path = Path(self.tmp_dir.name)

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

    def test_last_published_is_used(self):
        md_file = self.tmp_path / "post.md"
        md_file.write_text("Body", encoding="utf-8")

        add_frontmatter_to_file(md_file, file_layout="post", last_published="2026-08-29")

        result = md_file.read_text(encoding="utf-8")
        self.assertIn("layout: post", result)
        self.assertIn("last_published: \"2026-08-29\"", result)

    def test_section_is_written_when_provided(self):
        md_file = self.tmp_path / "journey" / "design" / "design.md"
        md_file.parent.mkdir(parents=True, exist_ok=True)
        md_file.write_text("Body", encoding="utf-8")

        add_frontmatter_to_file(md_file, file_layout="section", section="journey", include_permalink=True)

        result = md_file.read_text(encoding="utf-8")
        self.assertIn("section: journey", result)
        self.assertIn("layout: section", result)

    def test_pre_existing_frontmatter_is_replaced_not_stacked(self):
        # Obsidian plugins like Excalidraw prepend their own frontmatter block;
        # Jekyll only tolerates one per file.
        md_file = self.tmp_path / "drawing.excalidraw.md"
        md_file.write_text("---\nexcalidraw-plugin: parsed\n---\nBody", encoding="utf-8")

        add_frontmatter_to_file(md_file)

        result = md_file.read_text(encoding="utf-8")
        self.assertEqual(result.count("---\n"), 2)
        self.assertNotIn("excalidraw-plugin", result)


if __name__ == '__main__':
    unittest.main()
