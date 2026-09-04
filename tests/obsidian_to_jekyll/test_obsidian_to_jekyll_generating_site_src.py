import tempfile
import unittest
from pathlib import Path

import test_helpers
from scripts.obsidian_to_jekyll import (
    ObsidianToJekyllConverter,
)


def start_next_run(converter: ObsidianToJekyllConverter) -> None:
    """Persist whatever this run produced, then begin a fresh run —
    mirrors exactly what a second real invocation of the script would see."""
    converter.site_sync.save()
    converter.begin_run()


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

    def test_post_filename_with_spaces_and_mixed_case_is_slugified(self):
        posts_dir = self.converter.obsidian_vault_location / "posts"
        posts_dir.mkdir()
        (posts_dir / "2026-08-27 journey Whiteboard Showing.md").write_text("content", encoding="utf-8")

        self.converter.copy_vault_resources()

        self.assertTrue(
            (self.converter.output_location / "_posts" / "2026-08-27-journey-whiteboard-showing.md").exists()
        )
        self.assertFalse(
            (self.converter.output_location / "_posts" / "2026-08-27 journey Whiteboard Showing.md").exists()
        )

    def test_non_post_directories_are_not_slugified(self):
        # slugification is scoped to _posts only — an "about" note keeps its
        # original filename, since other notes aren't subject to Jekyll's
        # _posts naming rule and existing wikilinks may depend on the name.
        about_dir = self.converter.obsidian_vault_location / "about"
        about_dir.mkdir()
        (about_dir / "My About Page.md").write_text("about me", encoding="utf-8")

        self.converter.copy_vault_resources()

        self.assertTrue((self.converter.output_location / "about" / "My About Page.md").exists())

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

    def test_images_in_posts_directory_are_excluded_from_underscore_posts(self):
        # Jekyll tries to read every file under _posts as UTF-8 front matter and
        # blows up on binary content, so image assets must never land there.
        posts_dir = self.converter.obsidian_vault_location / "posts" / "2026" / "08"
        posts_dir.mkdir(parents=True)
        (posts_dir / "screenshot.png").write_bytes(b"\x89PNG\r\n\x1a\nfake-bytes")

        self.converter.copy_vault_resources()

        self.assertFalse((self.converter.output_location / "_posts" / "2026" / "08" / "screenshot.png").exists())

    def test_other_image_extensions_in_posts_are_also_excluded_from_underscore_posts(self):
        posts_dir = self.converter.obsidian_vault_location / "posts"
        posts_dir.mkdir()
        (posts_dir / "photo.jpg").write_bytes(b"fake-jpg")
        (posts_dir / "photo.jpeg").write_bytes(b"fake-jpeg")
        (posts_dir / "photo.gif").write_bytes(b"fake-gif")
        (posts_dir / "screenshot.png").write_bytes(b"\x89PNG\r\n\x1a\nfake-bytes")

        self.converter.copy_vault_resources()

        output_posts = self.converter.output_location / "_posts"
        self.assertFalse((output_posts / "photo.jpg").exists())
        self.assertFalse((output_posts / "photo.jpeg").exists())
        self.assertFalse((output_posts / "photo.gif").exists())
        self.assertFalse((output_posts / "screenshot.png").exists())

    def test_excalidraw_svg_in_posts_is_excluded_from_underscore_posts(self):
        # mirrors the png/jpg/gif exclusion above — an excalidraw drawing's
        # auto-exported SVG living inside posts/ shouldn't land in _posts
        # either; it belongs only in assets/images via the dedicated copy step.
        posts_dir = self.converter.obsidian_vault_location / "posts"
        posts_dir.mkdir()
        (posts_dir / "diagram.excalidraw.svg").write_text("<svg></svg>", encoding="utf-8")

        self.converter.copy_vault_resources()

        self.assertFalse((self.converter.output_location / "_posts" / "diagram.excalidraw.svg").exists())

    def test_markdown_alongside_excluded_image_in_posts_is_still_copied_to_underscore_posts(self):
        posts_dir = self.converter.obsidian_vault_location / "posts"
        posts_dir.mkdir()
        (posts_dir / "screenshot.png").write_bytes(b"fake-bytes")
        (posts_dir / "entry.md").write_text("body text", encoding="utf-8")

        self.converter.copy_vault_resources()

        self.assertTrue((self.converter.output_location / "_posts" / "entry.md").exists())
        self.assertFalse((self.converter.output_location / "_posts" / "screenshot.png").exists())

    def test_images_outside_posts_directory_are_also_excluded_from_underscore_posts(self):
        # Images are handled exclusively by copy_vault_images_into_assets_directory,
        # which buckets them under assets/. If copy_vault_resources also copied
        # them here, they'd be duplicated in the output (once under their
        # original vault folder, once under assets/).
        gallery_dir = self.converter.obsidian_vault_location / "gallery"
        gallery_dir.mkdir()
        (gallery_dir / "picture.png").write_bytes(b"fake-bytes")

        self.converter.copy_vault_resources()

        self.assertFalse((self.converter.output_location / "gallery" / "picture.png").exists())

    def test_recurring_run_is_idempotent(self):
        posts_dir = self.converter.obsidian_vault_location / "posts"
        posts_dir.mkdir()
        (posts_dir / "hello.md").write_text("hi", encoding="utf-8")
        self.converter.copy_vault_resources()  # first-time setup

        start_next_run(self.converter)  # recurring setup: persist + reload from disk
        self.converter.copy_vault_resources()  # should not raise, nothing changed

        self.assertEqual(self.converter.site_sync.changed_dest_paths, [])
        self.assertTrue((self.converter.output_location / "_posts" / "hello.md").exists())


class TestCopyVaultImagesIntoAssetsDirectory(unittest.TestCase):
    """Covers both first-time setup (fresh converter, empty manifest) and
    recurring setup (same converter, manifest reloaded from disk via start_next_run)."""

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)
        self.converter = test_helpers.make_converter(Path(self.tmp_dir.name))
        self.converter.begin_run()

    def test_image_is_bucketed_by_top_level_vault_directory(self):
        buttons_dir = self.converter.obsidian_vault_location / "88x31" / "memes-as-buttons"
        buttons_dir.mkdir(parents=True)
        (buttons_dir / "free-real-estate.svg").write_text("<svg></svg>", encoding="utf-8")

        self.converter.copy_vault_images_into_assets_directory()

        self.assertTrue(
            (self.converter.output_location / "assets" / "88x31" / "free-real-estate.svg").exists()
        )

    def test_vault_images_inside_assets_directory_are_not_copied_as_asset_asset_image(self):
        buttons_dir = self.converter.obsidian_vault_location / "assets" / "88x31" / "memes-as-buttons"
        buttons_dir.mkdir(parents=True)
        (buttons_dir / "free-real-estate.svg").write_text("<svg></svg>", encoding="utf-8")

        self.converter.copy_vault_images_into_assets_directory()

        self.assertFalse(
            (self.converter.output_location / "assets" / "assets" / "88x31" / "free-real-estate.svg").exists()
        )
        self.assertTrue(
            (self.converter.output_location / "assets" / "88x31" / "free-real-estate.svg").exists()
        )

    def test_deeply_nested_image_is_flattened_into_top_level_bucket(self):
        posts_dir = self.converter.obsidian_vault_location / "posts" / "2026" / "08"
        posts_dir.mkdir(parents=True)
        (posts_dir / "pagination-test-screenshot.png").write_bytes(b"fake-png-bytes")

        self.converter.copy_vault_images_into_assets_directory()

        self.assertTrue(
            (self.converter.output_location / "assets" / "posts" / "pagination-test-screenshot.png").exists()
        )

    def test_root_level_image_has_no_parent_directory_bucket(self):
        (self.converter.obsidian_vault_location / "favicon.svg").write_text("<svg></svg>", encoding="utf-8")

        self.converter.copy_vault_images_into_assets_directory()

        self.assertTrue((self.converter.output_location / "assets" / "favicon.svg").exists())

    def test_unchanged_image_is_skipped_on_recurring_run(self):
        buttons_dir = self.converter.obsidian_vault_location / "88x31" / "memes-as-buttons"
        buttons_dir.mkdir(parents=True)
        (buttons_dir / "free-real-estate.svg").write_text("<svg></svg>", encoding="utf-8")
        self.converter.copy_vault_images_into_assets_directory()  # first-time setup

        start_next_run(self.converter)  # recurring setup: persist + reload from disk
        self.converter.copy_vault_images_into_assets_directory()  # unchanged content

        self.assertEqual(self.converter.site_sync.changed_dest_paths, [])

    def test_changed_image_is_recopied_on_recurring_run(self):
        image = self.converter.obsidian_vault_location / "88x31" / "free-real-estate.svg"
        image.parent.mkdir(parents=True)
        image.write_text("original", encoding="utf-8")
        self.converter.copy_vault_images_into_assets_directory()

        start_next_run(self.converter)
        image.write_text("updated", encoding="utf-8")
        self.converter.copy_vault_images_into_assets_directory()

        dest = self.converter.output_location / "assets" / "88x31" / "free-real-estate.svg"
        self.assertEqual(dest.read_text(encoding="utf-8"), "updated")
        self.assertIn(dest, self.converter.site_sync.changed_dest_paths)

    def test_non_image_files_are_ignored(self):
        notes_dir = self.converter.obsidian_vault_location / "about"
        notes_dir.mkdir(parents=True)
        (notes_dir / "notes.md").write_text("hello", encoding="utf-8")

        self.converter.copy_vault_images_into_assets_directory()

        self.assertFalse((self.converter.output_location / "assets" / "about" / "notes.md").exists())


if __name__ == '__main__':
    unittest.main()
