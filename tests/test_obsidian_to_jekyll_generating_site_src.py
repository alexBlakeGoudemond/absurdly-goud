import tempfile
import unittest
from pathlib import Path
from textwrap import dedent

import test_helpers
from scripts.jekyll_frontmatter import add_frontmatter_to_file
from scripts.obsidian_to_jekyll import (
    ObsidianToJekyllConverter,
    process_markdown_for_jekyll,
    find_section,
)
from scripts.wikilinks import build_note_path_lookup


def start_next_run(converter: ObsidianToJekyllConverter) -> None:
    """Persist whatever this run produced, then begin a fresh run —
    mirrors exactly what a second real invocation of the script would see."""
    converter.site_sync.save()
    converter.begin_run()


class TestFindSection(unittest.TestCase):

    def test_returns_matching_ancestor_folder(self):
        result = find_section(Path("vision/design/website-design.md"), ["vision"])
        self.assertEqual(result, "vision")

    def test_returns_none_when_no_ancestor_matches(self):
        result = find_section(Path("about.md"), ["vision"])
        self.assertIsNone(result)

    def test_only_matches_configured_folders(self):
        result = find_section(Path("progress/update.md"), ["vision"])
        self.assertIsNone(result)


class TestAddFrontmatterToMarkdownFiles(unittest.TestCase):
    """Exercises the orchestration logic — which files get frontmatter injected
    based on changed_dest_paths, name, and extension — not add_frontmatter_to_file itself."""

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)
        self.tmp_path = Path(self.tmp_dir.name)
        self.converter = test_helpers.make_converter(Path(self.tmp_dir.name))
        self.converter.begin_run()
        self.note_lookup = build_note_path_lookup(Path(self.tmp_dir.name))

    def test_changed_markdown_file_gets_frontmatter(self):
        dest = self.converter.output_location / "hello-world.md"
        dest.write_text("# Hello", encoding="utf-8")
        self.converter.site_sync.changed_dest_paths = [dest]

        self.converter.parse_markdown_files_for_jekyll(self.note_lookup)

        result = dest.read_text(encoding="utf-8")
        self.assertIn("layout: default", result)
        # title is display_title_from_slug'd (slug -> Title Case), not the raw slug —
        # this assertion previously expected the raw slug, which the code has
        # never actually produced; see TestDisplayTitleFromSlug for that unit directly.
        self.assertIn("title: \"Hello World\"", result)

    def test_about_md_gets_permalink(self):
        dest = self.converter.output_location / "about.md"
        dest.write_text("About me", encoding="utf-8")
        self.converter.site_sync.changed_dest_paths = [dest]

        self.converter.parse_markdown_files_for_jekyll(self.note_lookup)

        result = dest.read_text(encoding="utf-8")
        self.assertIn("permalink: /about/", result)

    def test_section_file_gets_section_layout_and_frontmatter(self):
        section_dir = self.converter.output_location / "vision" / "design"
        section_dir.mkdir(parents=True)
        dest = section_dir / "website-design.md"
        dest.write_text("Design notes", encoding="utf-8")
        self.converter.site_sync.changed_dest_paths = [dest]

        self.converter.parse_markdown_files_for_jekyll(self.note_lookup)

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


class TestMarkdownFileConversion(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)
        self.converter = test_helpers.make_converter(Path(self.tmp_dir.name))
        self.converter.begin_run()
        self.note_lookup = build_note_path_lookup(Path(self.tmp_dir.name))

    def test_ignored_files_are_skipped(self):
        for name in self.converter.IGNORED_FRONTMATTER_FILES:
            dest = self.converter.output_location / name
            dest.write_text("original content", encoding="utf-8")
            self.converter.site_sync.changed_dest_paths = [dest]

            self.converter.parse_markdown_files_for_jekyll(self.note_lookup)

            self.assertEqual(dest.read_text(encoding="utf-8"), "original content")

    def test_non_markdown_files_are_skipped(self):
        dest = self.converter.output_location / "style.css"
        dest.write_text("body {}", encoding="utf-8")
        self.converter.site_sync.changed_dest_paths = [dest]

        self.converter.parse_markdown_files_for_jekyll(self.note_lookup)

        self.assertEqual(dest.read_text(encoding="utf-8"), "body {}")

    def test_cache_hit_file_not_in_changed_dest_paths_is_untouched(self):
        # simulates a recurring run where this file was a cache hit (unchanged) —
        # it should NOT reappear in changed_dest_paths, and must not get double-frontmatter
        dest = self.converter.output_location / "post.md"
        original = "---\nlayout: default\ntitle: post\n---\n\nBody"
        dest.write_text(original, encoding="utf-8")
        self.converter.site_sync.changed_dest_paths = []  # nothing changed this run

        self.converter.parse_markdown_files_for_jekyll(self.note_lookup)

        self.assertEqual(dest.read_text(encoding="utf-8"), original)

    def test_multiple_changed_files_all_get_processed(self):
        dest_a = self.converter.output_location / "post-a.md"
        dest_b = self.converter.output_location / "post-b.md"
        dest_a.write_text("A", encoding="utf-8")
        dest_b.write_text("B", encoding="utf-8")
        self.converter.site_sync.changed_dest_paths = [dest_a, dest_b]

        self.converter.parse_markdown_files_for_jekyll(self.note_lookup)

        # title is display_title_from_slug'd (slug -> Title Case) — see note above.
        self.assertIn("title: \"Post A\"", dest_a.read_text(encoding="utf-8"))
        self.assertIn("title: \"Post B\"", dest_b.read_text(encoding="utf-8"))


class TestMarkdownImageNotationConversion(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)
        self.tmp_path = Path(self.tmp_dir.name)
        self.converter = test_helpers.make_converter(Path(self.tmp_dir.name))
        self.converter.begin_run()
        self.note_lookup = build_note_path_lookup(Path(self.tmp_dir.name))

    def test_process_one_markdown_image_yields_one_jekyll_includes_syntax_in_file(self):
        dest = self.converter.output_location / "post.md"
        dest.write_text("![Alt text](image.png)", encoding="utf-8")
        self.converter.site_sync.changed_dest_paths = [dest]

        process_markdown_for_jekyll(dest, self.note_lookup)

        result = dest.read_text(encoding="utf-8")
        expected_syntax = """
        {% include image.html
            src="image.png"
            alt="Alt text"
            title="Alt text"
        %}
        """
        self.assertIn(dedent(expected_syntax), result)

    def test_process_two_markdown_image_yields_two_jekyll_includes_syntax_in_file(self):
        dest = self.converter.output_location / "post.md"
        dest.write_text("![Alt text 1](image1.png)\n![Alt text 2](image2.png)", encoding="utf-8")
        self.converter.site_sync.changed_dest_paths = [dest]

        process_markdown_for_jekyll(dest, self.note_lookup)

        result = dest.read_text(encoding="utf-8")
        expected_syntax_1 = """
            {% include image.html
                src="image1.png"
                alt="Alt text 1"
                title="Alt text 1"
            %}
            """
        expected_syntax_2 = """
            {% include image.html
                src="image2.png"
                alt="Alt text 2"
                title="Alt text 2"
            %}
            """
        self.assertIn(dedent(expected_syntax_1), result)
        self.assertIn(dedent(expected_syntax_2), result)


class TestCopyJekyllResources(unittest.TestCase):
    """Covers both first-time setup (fresh converter, empty manifest) and
    recurring setup (same converter, manifest reloaded from disk via start_next_run)."""

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)
        self.converter = test_helpers.make_converter(Path(self.tmp_dir.name))
        self.converter.begin_run()  # first-time setup: empty old_manifest, no disk state yet

    def test_included_file_is_copied(self):
        (self.converter.source_location / "CNAME").write_text("example.com", encoding="utf-8")

        self.converter.copy_jekyll_resources()

        self.assertTrue((self.converter.output_location / "CNAME").exists())

    def test_included_directory_is_copied(self):
        assets_dir = self.converter.source_location / "assets"
        assets_dir.mkdir()
        (assets_dir / "style.css").write_text("body {}", encoding="utf-8")

        self.converter.copy_jekyll_resources()

        self.assertTrue((self.converter.output_location / "assets" / "style.css").exists())

    def test_non_included_item_is_ignored(self):
        (self.converter.source_location / "README.md").write_text("readme", encoding="utf-8")

        self.converter.copy_jekyll_resources()

        self.assertFalse((self.converter.output_location / "README.md").exists())

    def test_unchanged_file_is_skipped_on_recurring_run(self):
        (self.converter.source_location / "CNAME").write_text("example.com", encoding="utf-8")
        self.converter.copy_jekyll_resources()  # first-time setup

        start_next_run(self.converter)  # recurring setup: persist + reload from disk
        self.converter.copy_jekyll_resources()  # same source content, unchanged

        self.assertEqual(self.converter.site_sync.changed_dest_paths, [])

    def test_changed_file_is_recopied_on_recurring_run(self):
        cname = self.converter.source_location / "CNAME"
        cname.write_text("example.com", encoding="utf-8")
        self.converter.copy_jekyll_resources()  # first-time setup

        start_next_run(self.converter)  # recurring setup
        cname.write_text("changed.com", encoding="utf-8")
        self.converter.copy_jekyll_resources()

        self.assertEqual(len(self.converter.site_sync.changed_dest_paths), 1)
        self.assertEqual(
            (self.converter.output_location / "CNAME").read_text(encoding="utf-8"),
            "changed.com",
        )


class TestCopyVaultResources(unittest.TestCase):
    """copy_vault_resources uses sync_tree, so it's idempotent across recurring runs.
    Images inside posts/ are excluded here because Jekyll fails to build any binary
    file placed under _posts (it tries to parse every file there as UTF-8 front
    matter); images belong in assets/images instead, via copy_vault_images_into_assets_directory."""

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)
        self.converter = test_helpers.make_converter(Path(self.tmp_dir.name))
        self.converter.begin_run()

    def test_posts_directory_is_renamed_to_underscore_posts(self):
        posts_dir = self.converter.obsidian_vault_location / "posts"
        posts_dir.mkdir()
        (posts_dir / "hello.md").write_text("hi", encoding="utf-8")

        self.converter.copy_vault_resources()

        self.assertTrue((self.converter.output_location / "_posts" / "hello.md").exists())
        self.assertFalse((self.converter.output_location / "posts").exists())

    def test_obsidian_config_directory_is_ignored(self):
        obsidian_dir = self.converter.obsidian_vault_location / ".obsidian"
        obsidian_dir.mkdir()
        (obsidian_dir / "config.json").write_text("{}", encoding="utf-8")

        self.converter.copy_vault_resources()

        self.assertFalse((self.converter.output_location / ".obsidian").exists())

    def test_other_directories_are_copied_as_is(self):
        about_dir = self.converter.obsidian_vault_location / "about"
        about_dir.mkdir()
        (about_dir / "about.md").write_text("about me", encoding="utf-8")

        self.converter.copy_vault_resources()

        self.assertTrue((self.converter.output_location / "about" / "about.md").exists())

    def test_images_in_posts_directory_are_excluded(self):
        # Jekyll tries to read every file under _posts as UTF-8 front matter and
        # blows up on binary content, so image assets must never land there.
        posts_dir = self.converter.obsidian_vault_location / "posts" / "2026" / "08"
        posts_dir.mkdir(parents=True)
        (posts_dir / "screenshot.png").write_bytes(b"\x89PNG\r\n\x1a\nfake-bytes")

        self.converter.copy_vault_resources()

        self.assertFalse((self.converter.output_location / "_posts" / "2026" / "08" / "screenshot.png").exists())

    def test_other_image_extensions_in_posts_are_also_excluded(self):
        posts_dir = self.converter.obsidian_vault_location / "posts"
        posts_dir.mkdir()
        (posts_dir / "photo.jpg").write_bytes(b"fake-jpg")
        (posts_dir / "photo.jpeg").write_bytes(b"fake-jpeg")
        (posts_dir / "photo.gif").write_bytes(b"fake-gif")

        self.converter.copy_vault_resources()

        output_posts = self.converter.output_location / "_posts"
        self.assertFalse((output_posts / "photo.jpg").exists())
        self.assertFalse((output_posts / "photo.jpeg").exists())
        self.assertFalse((output_posts / "photo.gif").exists())

    def test_markdown_alongside_excluded_image_in_posts_is_still_copied(self):
        posts_dir = self.converter.obsidian_vault_location / "posts"
        posts_dir.mkdir()
        (posts_dir / "screenshot.png").write_bytes(b"fake-bytes")
        (posts_dir / "entry.md").write_text("body text", encoding="utf-8")

        self.converter.copy_vault_resources()

        self.assertTrue((self.converter.output_location / "_posts" / "entry.md").exists())
        self.assertFalse((self.converter.output_location / "_posts" / "screenshot.png").exists())

    def test_images_outside_posts_directory_are_not_excluded(self):
        # exclude_suffixes is only applied to the posts/ -> _posts sync; other
        # top-level vault directories should copy images through untouched.
        gallery_dir = self.converter.obsidian_vault_location / "gallery"
        gallery_dir.mkdir()
        (gallery_dir / "picture.png").write_bytes(b"fake-bytes")

        self.converter.copy_vault_resources()

        self.assertTrue((self.converter.output_location / "gallery" / "picture.png").exists())

    def test_recurring_run_is_idempotent(self):
        posts_dir = self.converter.obsidian_vault_location / "posts"
        posts_dir.mkdir()
        (posts_dir / "hello.md").write_text("hi", encoding="utf-8")
        self.converter.copy_vault_resources()  # first-time setup

        start_next_run(self.converter)  # recurring setup: persist + reload from disk
        self.converter.copy_vault_resources()  # should not raise, nothing changed

        self.assertEqual(self.converter.site_sync.changed_dest_paths, [])
        self.assertTrue((self.converter.output_location / "_posts" / "hello.md").exists())


class TestCollectImagesInAssetsDirectory(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)
        self.converter = test_helpers.make_converter(Path(self.tmp_dir.name))
        self.converter.begin_run()

    def test_png_is_copied_to_assets_images(self):
        (self.converter.obsidian_vault_location / "photo.png").write_bytes(b"fake-png-bytes")

        self.converter.copy_vault_images_into_assets_directory()

        dest = self.converter.output_location / "assets" / "images" / "photo.png"
        self.assertTrue(dest.exists())
        self.assertEqual(dest.read_bytes(), b"fake-png-bytes")

    def test_non_png_files_are_ignored(self):
        (self.converter.obsidian_vault_location / "notes.md").write_text("hello", encoding="utf-8")

        self.converter.copy_vault_images_into_assets_directory()

        self.assertFalse((self.converter.output_location / "assets" / "images" / "notes.md").exists())

    def test_nested_png_is_found_via_rglob(self):
        nested_dir = self.converter.obsidian_vault_location / "posts" / "2026" / "08"
        nested_dir.mkdir(parents=True)
        (nested_dir / "screenshot.png").write_bytes(b"nested-bytes")

        self.converter.copy_vault_images_into_assets_directory()

        dest = self.converter.output_location / "assets" / "images" / "screenshot.png"
        self.assertTrue(dest.exists())

    def test_unchanged_image_is_skipped_on_recurring_run(self):
        (self.converter.obsidian_vault_location / "photo.png").write_bytes(b"same-bytes")
        self.converter.copy_vault_images_into_assets_directory()  # first-time setup

        start_next_run(self.converter)  # recurring setup
        self.converter.copy_vault_images_into_assets_directory()

        self.assertEqual(self.converter.site_sync.changed_dest_paths, [])

    def test_changed_image_is_recopied_on_recurring_run(self):
        image = self.converter.obsidian_vault_location / "photo.png"
        image.write_bytes(b"original-bytes")
        self.converter.copy_vault_images_into_assets_directory()

        start_next_run(self.converter)
        image.write_bytes(b"updated-bytes")
        self.converter.copy_vault_images_into_assets_directory()

        dest = self.converter.output_location / "assets" / "images" / "photo.png"
        self.assertEqual(dest.read_bytes(), b"updated-bytes")
        self.assertIn(dest, self.converter.site_sync.changed_dest_paths)


if __name__ == '__main__':
    unittest.main()
