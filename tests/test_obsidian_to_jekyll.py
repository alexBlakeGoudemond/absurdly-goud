import unittest
import argparse
import tempfile
from pathlib import Path
from textwrap import dedent

from scripts import obsidian_to_jekyll
from scripts.obsidian_to_jekyll import (
    extract_command_line_arguments,
    ObsidianToJekyllConverter,
    save_manifest,
    convert_markdown_image_notation_to_jekyll_includes_image_notation,
    process_image_notation_in_markdown_file,
)


def make_args(vault: str, out_dir: str, src_root: str) -> argparse.Namespace:
    return argparse.Namespace(vault=vault, out_dir=out_dir, src_root=Path(src_root))


def make_converter(tmp_path: Path) -> ObsidianToJekyllConverter:
    vault = tmp_path / "vault"
    output = tmp_path / "output"
    source = tmp_path / "source"
    vault.mkdir()
    output.mkdir()
    source.mkdir()
    return ObsidianToJekyllConverter(vault, output, source)


def start_next_run(converter: ObsidianToJekyllConverter) -> None:
    """Persist whatever this run produced, then begin a fresh run —
    mirrors exactly what a second real invocation of the script would see."""
    save_manifest(converter.manifest_path, converter.new_manifest)
    converter.begin_run()


class TestExtractCommandLineArguments(unittest.TestCase):

    def test_returns_paths_for_explicit_args(self):
        args = make_args(vault="my_vault", out_dir="site_src", src_root="some/root")

        vault, out, src = extract_command_line_arguments(args)

        self.assertEqual(vault, Path("my_vault"))
        self.assertEqual(out, Path("site_src"))
        self.assertEqual(src, Path("some/root"))

    def test_src_root_defaults_to_script_parent_when_dot(self):
        args = make_args(vault="v", out_dir="o", src_root=".")

        _, _, src = extract_command_line_arguments(args)

        expected = Path(obsidian_to_jekyll.__file__).resolve().parents[1]

        self.assertEqual(src, expected)

    def test_return_types_are_path_objects(self):
        args = make_args(vault="v", out_dir="o", src_root="r")

        result = extract_command_line_arguments(args)

        self.assertTrue(all(isinstance(p, Path) for p in result))
        self.assertEqual(len(result), 3)


class TestExtractTitleFromFileName(unittest.TestCase):

    def test_strips_date_prefix_and_extension(self):
        title = ObsidianToJekyllConverter.extract_title_from_file_name("2026-08-19-hello-world.md")
        self.assertEqual(title, "hello-world")

    def test_no_date_prefix_still_strips_extension(self):
        title = ObsidianToJekyllConverter.extract_title_from_file_name("about.md")
        self.assertEqual(title, "about")

    def test_non_md_extension_is_untouched(self):
        title = ObsidianToJekyllConverter.extract_title_from_file_name("home.mdx")
        self.assertEqual(title, "home.mdx")


class TestAddFrontmatterToFile(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)
        self.tmp_path = Path(self.tmp_dir.name)

    def test_adds_default_layout_frontmatter(self):
        md_file = self.tmp_path / "2026-08-19-hello-world.md"
        md_file.write_text("# Hello World", encoding="utf-8")

        ObsidianToJekyllConverter.add_frontmatter_to_file(md_file)

        result = md_file.read_text(encoding="utf-8")
        self.assertIn("layout: default", result)
        self.assertIn("title: hello-world", result)
        self.assertIn("# Hello World", result)

    def test_permalink_included_when_requested(self):
        md_file = self.tmp_path / "about.md"
        md_file.write_text("About me", encoding="utf-8")

        ObsidianToJekyllConverter.add_frontmatter_to_file(md_file, include_permalink=True)

        result = md_file.read_text(encoding="utf-8")
        self.assertIn("permalink: /about/", result)

    def test_permalink_omitted_by_default(self):
        md_file = self.tmp_path / "post.md"
        md_file.write_text("Post body", encoding="utf-8")

        ObsidianToJekyllConverter.add_frontmatter_to_file(md_file)

        result = md_file.read_text(encoding="utf-8")
        self.assertNotIn("permalink:", result)

    def test_custom_layout_is_used(self):
        md_file = self.tmp_path / "post.md"
        md_file.write_text("Body", encoding="utf-8")

        ObsidianToJekyllConverter.add_frontmatter_to_file(md_file, file_layout="post")

        result = md_file.read_text(encoding="utf-8")
        self.assertIn("layout: post", result)


class TestCopyJekyllResources(unittest.TestCase):
    """Covers both first-time setup (fresh converter, empty manifest) and
    recurring setup (same converter, manifest reloaded from disk via start_next_run)."""

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)
        self.converter = make_converter(Path(self.tmp_dir.name))
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

        self.assertEqual(self.converter.changed_dest_paths, [])

    def test_changed_file_is_recopied_on_recurring_run(self):
        cname = self.converter.source_location / "CNAME"
        cname.write_text("example.com", encoding="utf-8")
        self.converter.copy_jekyll_resources()  # first-time setup

        start_next_run(self.converter)  # recurring setup
        cname.write_text("changed.com", encoding="utf-8")
        self.converter.copy_jekyll_resources()

        self.assertEqual(len(self.converter.changed_dest_paths), 1)
        self.assertEqual(
            (self.converter.output_location / "CNAME").read_text(encoding="utf-8"),
            "changed.com",
        )


class TestCopyVaultResources(unittest.TestCase):
    """NOTE: copy_vault_resources currently uses shutil.copytree, not sync_tree —
    it isn't idempotent and will raise FileExistsError on a recurring run against
    a non-empty output dir. Covers first-time setup only until it's switched to sync_tree."""

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)
        self.converter = make_converter(Path(self.tmp_dir.name))
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


class TestSyncFile(unittest.TestCase):
    """Covers first-time setup, recurring/unchanged, recurring/changed, and rename cases."""

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)
        self.converter = make_converter(Path(self.tmp_dir.name))
        self.converter.begin_run()

    def test_new_file_is_copied_and_recorded(self):
        source = self.converter.obsidian_vault_location / "note.md"
        source.write_text("hello", encoding="utf-8")
        dest = self.converter.output_location / "note.md"

        self.converter.sync_file(source, dest)

        self.assertTrue(dest.exists())
        self.assertEqual(dest.read_text(encoding="utf-8"), "hello")
        self.assertIn(dest, self.converter.changed_dest_paths)
        self.assertIn(str(source), self.converter.new_manifest)

    def test_unchanged_file_is_skipped_on_recurring_run(self):
        source = self.converter.obsidian_vault_location / "note.md"
        source.write_text("hello", encoding="utf-8")
        dest = self.converter.output_location / "note.md"
        self.converter.sync_file(source, dest)  # first-time setup

        start_next_run(self.converter)  # recurring setup
        self.converter.sync_file(source, dest)

        self.assertEqual(self.converter.changed_dest_paths, [])

    def test_changed_file_is_recopied_on_recurring_run(self):
        source = self.converter.obsidian_vault_location / "note.md"
        source.write_text("hello", encoding="utf-8")
        dest = self.converter.output_location / "note.md"
        self.converter.sync_file(source, dest)

        start_next_run(self.converter)
        source.write_text("updated", encoding="utf-8")
        self.converter.sync_file(source, dest)

        self.assertEqual(dest.read_text(encoding="utf-8"), "updated")
        self.assertIn(dest, self.converter.changed_dest_paths)

    def test_renamed_source_removes_old_dest_on_recurring_run(self):
        source = self.converter.obsidian_vault_location / "note.md"
        source.write_text("hello", encoding="utf-8")
        old_dest = self.converter.output_location / "old_location.md"
        self.converter.sync_file(source, old_dest)

        start_next_run(self.converter)
        new_dest = self.converter.output_location / "new_location.md"
        self.converter.sync_file(source, new_dest)

        self.assertFalse(old_dest.exists())
        self.assertTrue(new_dest.exists())


class TestPruneStaleFiles(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)
        self.converter = make_converter(Path(self.tmp_dir.name))
        self.converter.begin_run()

    def test_deletes_output_for_source_removed_on_recurring_run(self):
        source = self.converter.obsidian_vault_location / "gone.md"
        source.write_text("content", encoding="utf-8")
        dest = self.converter.output_location / "gone.md"
        self.converter.sync_file(source, dest)  # first-time setup

        start_next_run(self.converter)  # recurring setup
        source.unlink()  # source no longer present this run — never re-synced
        self.converter.prune_stale_files()

        self.assertFalse(dest.exists())

    def test_keeps_output_still_present_on_recurring_run(self):
        source = self.converter.obsidian_vault_location / "kept.md"
        source.write_text("content", encoding="utf-8")
        dest = self.converter.output_location / "kept.md"
        self.converter.sync_file(source, dest)

        start_next_run(self.converter)
        self.converter.sync_file(source, dest)  # still present, re-synced (cache hit)
        self.converter.prune_stale_files()

        self.assertTrue(dest.exists())


class TestCollectImagesInAssetsDirectory(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)
        self.converter = make_converter(Path(self.tmp_dir.name))
        self.converter.begin_run()

    def test_png_is_copied_to_assets_images(self):
        (self.converter.obsidian_vault_location / "photo.png").write_bytes(b"fake-png-bytes")

        self.converter.collect_images_in_assets_directory()

        dest = self.converter.output_location / "assets" / "images" / "photo.png"
        self.assertTrue(dest.exists())
        self.assertEqual(dest.read_bytes(), b"fake-png-bytes")

    def test_non_png_files_are_ignored(self):
        (self.converter.obsidian_vault_location / "notes.md").write_text("hello", encoding="utf-8")

        self.converter.collect_images_in_assets_directory()

        self.assertFalse((self.converter.output_location / "assets" / "images" / "notes.md").exists())

    def test_nested_png_is_found_via_rglob(self):
        nested_dir = self.converter.obsidian_vault_location / "posts" / "2026" / "08"
        nested_dir.mkdir(parents=True)
        (nested_dir / "screenshot.png").write_bytes(b"nested-bytes")

        self.converter.collect_images_in_assets_directory()

        dest = self.converter.output_location / "assets" / "images" / "screenshot.png"
        self.assertTrue(dest.exists())

    def test_unchanged_image_is_skipped_on_recurring_run(self):
        (self.converter.obsidian_vault_location / "photo.png").write_bytes(b"same-bytes")
        self.converter.collect_images_in_assets_directory()  # first-time setup

        start_next_run(self.converter)  # recurring setup
        self.converter.collect_images_in_assets_directory()

        self.assertEqual(self.converter.changed_dest_paths, [])

    def test_changed_image_is_recopied_on_recurring_run(self):
        image = self.converter.obsidian_vault_location / "photo.png"
        image.write_bytes(b"original-bytes")
        self.converter.collect_images_in_assets_directory()

        start_next_run(self.converter)
        image.write_bytes(b"updated-bytes")
        self.converter.collect_images_in_assets_directory()

        dest = self.converter.output_location / "assets" / "images" / "photo.png"
        self.assertEqual(dest.read_bytes(), b"updated-bytes")
        self.assertIn(dest, self.converter.changed_dest_paths)


class TestAddFrontmatterToMarkdownFiles(unittest.TestCase):
    """Exercises the orchestration logic — which files get frontmatter injected
    based on changed_dest_paths, name, and extension — not add_frontmatter_to_file itself."""

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)
        self.converter = make_converter(Path(self.tmp_dir.name))
        self.converter.begin_run()

    def test_changed_markdown_file_gets_frontmatter(self):
        dest = self.converter.output_location / "hello-world.md"
        dest.write_text("# Hello", encoding="utf-8")
        self.converter.changed_dest_paths = [dest]

        self.converter.add_frontmatter_to_markdown_files()

        result = dest.read_text(encoding="utf-8")
        self.assertIn("layout: default", result)
        self.assertIn("title: hello-world", result)

    def test_about_md_gets_permalink(self):
        dest = self.converter.output_location / "about.md"
        dest.write_text("About me", encoding="utf-8")
        self.converter.changed_dest_paths = [dest]

        self.converter.add_frontmatter_to_markdown_files()

        result = dest.read_text(encoding="utf-8")
        self.assertIn("permalink: /about/", result)

    def test_ignored_files_are_skipped(self):
        for name in self.converter.IGNORED_FRONTMATTER_FILES:
            dest = self.converter.output_location / name
            dest.write_text("original content", encoding="utf-8")
            self.converter.changed_dest_paths = [dest]

            self.converter.add_frontmatter_to_markdown_files()

            self.assertEqual(dest.read_text(encoding="utf-8"), "original content")

    def test_non_markdown_files_are_skipped(self):
        dest = self.converter.output_location / "style.css"
        dest.write_text("body {}", encoding="utf-8")
        self.converter.changed_dest_paths = [dest]

        self.converter.add_frontmatter_to_markdown_files()

        self.assertEqual(dest.read_text(encoding="utf-8"), "body {}")

    def test_cache_hit_file_not_in_changed_dest_paths_is_untouched(self):
        # simulates a recurring run where this file was a cache hit (unchanged) —
        # it should NOT reappear in changed_dest_paths, and must not get double-frontmatter
        dest = self.converter.output_location / "post.md"
        original = "---\nlayout: default\ntitle: post\n---\n\nBody"
        dest.write_text(original, encoding="utf-8")
        self.converter.changed_dest_paths = []  # nothing changed this run

        self.converter.add_frontmatter_to_markdown_files()

        self.assertEqual(dest.read_text(encoding="utf-8"), original)

    def test_multiple_changed_files_all_get_processed(self):
        dest_a = self.converter.output_location / "post-a.md"
        dest_b = self.converter.output_location / "post-b.md"
        dest_a.write_text("A", encoding="utf-8")
        dest_b.write_text("B", encoding="utf-8")
        self.converter.changed_dest_paths = [dest_a, dest_b]

        self.converter.add_frontmatter_to_markdown_files()

        self.assertIn("title: post-a", dest_a.read_text(encoding="utf-8"))
        self.assertIn("title: post-b", dest_b.read_text(encoding="utf-8"))

    def test_markdown_image_notation_gets_converted_to_jekyll_includes_file(self):
        actual_syntax = convert_markdown_image_notation_to_jekyll_includes_image_notation('image.png', 'Alt text')
        expected_syntax = """
        {% include image.html
            src="image.png"
            alt="Alt text"
            title="Alt text"
        %}
        """
        self.assertEqual(dedent(expected_syntax), actual_syntax)

    def test_process_one_markdown_image_yields_one_jekyll_includes_syntax_in_file(self):
        dest = self.converter.output_location / "post.md"
        dest.write_text("![Alt text](image.png)", encoding="utf-8")
        self.converter.changed_dest_paths = [dest]

        process_image_notation_in_markdown_file(dest)

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
        self.converter.changed_dest_paths = [dest]

        process_image_notation_in_markdown_file(dest)

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

if __name__ == '__main__':
    unittest.main()
