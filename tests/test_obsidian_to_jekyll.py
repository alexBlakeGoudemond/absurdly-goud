import unittest
import argparse
import tempfile
from pathlib import Path

from scripts import obsidian_to_jekyll
from scripts.obsidian_to_jekyll import (
    extract_command_line_arguments,
    extract_title_from_file_name,
    add_frontmatter_to_file,
    copy_jekyll_resources,
    copy_vault_resources,
)


def make_args(vault: str, out_dir: str, src_root: str) -> argparse.Namespace:
    return argparse.Namespace(vault=vault, out_dir=out_dir, src_root=Path(src_root))


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
    """Pure function — no filesystem needed, so no setUp/tearDown required."""

    def test_strips_date_prefix_and_extension(self):
        title = extract_title_from_file_name("2026-08-19-hello-world.md")
        self.assertEqual(title, "hello-world")

    def test_no_date_prefix_still_strips_extension(self):
        title = extract_title_from_file_name("about.md")
        self.assertEqual(title, "about")

    def test_non_md_extension_is_untouched(self):
        # exposes an existing bug: the regex `re.compile(r'.md')` has an
        # unescaped '.', so it matches ANY char + 'md', not just literal '.md'
        title = extract_title_from_file_name("home.mdx")
        self.assertEqual(title, "home.mdx")


class TestAddFrontmatterToFile(unittest.TestCase):
    """Touches the filesystem — use setUp/tearDown with a real temp dir,
    since unittest doesn't have pytest's tmp_path fixture built in."""

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)  # runs even if a test fails
        self.tmp_path = Path(self.tmp_dir.name)

    def test_adds_default_layout_frontmatter(self):
        md_file = self.tmp_path / "2026-08-19-hello-world.md"
        md_file.write_text("# Hello World", encoding="utf-8")

        add_frontmatter_to_file(md_file)

        result = md_file.read_text(encoding="utf-8")
        self.assertIn("layout: default", result)
        self.assertIn("title: hello-world", result)
        self.assertIn("# Hello World", result)

    def test_permalink_included_when_requested(self):
        md_file = self.tmp_path / "about.md"
        md_file.write_text("About me", encoding="utf-8")

        add_frontmatter_to_file(md_file, include_permalink=True)

        result = md_file.read_text(encoding="utf-8")
        self.assertIn("permalink: /about/", result)

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


class TestCopyJekyllResources(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)
        self.source = Path(self.tmp_dir.name) / "source"
        self.output = Path(self.tmp_dir.name) / "output"
        self.source.mkdir()
        self.output.mkdir()

    def test_included_file_is_copied(self):
        (self.source / "CNAME").write_text("example.com", encoding="utf-8")

        copy_jekyll_resources(self.source, self.output)

        self.assertTrue((self.output / "CNAME").exists())

    def test_included_directory_is_copied(self):
        (self.source / "assets").mkdir()
        (self.source / "assets" / "style.css").write_text("body {}", encoding="utf-8")

        copy_jekyll_resources(self.source, self.output)

        self.assertTrue((self.output / "assets" / "style.css").exists())

    def test_non_included_item_is_ignored(self):
        (self.source / "README.md").write_text("readme", encoding="utf-8")

        copy_jekyll_resources(self.source, self.output)

        self.assertFalse((self.output / "README.md").exists())


class TestCopyVaultResources(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)
        self.vault = Path(self.tmp_dir.name) / "vault"
        self.output = Path(self.tmp_dir.name) / "output"
        self.vault.mkdir()
        self.output.mkdir()

    def test_posts_directory_is_renamed_to_underscore_posts(self):
        (self.vault / "posts").mkdir()
        (self.vault / "posts" / "hello.md").write_text("hi", encoding="utf-8")

        copy_vault_resources(self.vault, self.output)

        self.assertTrue((self.output / "_posts" / "hello.md").exists())
        self.assertFalse((self.output / "posts").exists())

    def test_obsidian_config_directory_is_ignored(self):
        (self.vault / ".obsidian").mkdir()
        (self.vault / ".obsidian" / "config.json").write_text("{}", encoding="utf-8")

        copy_vault_resources(self.vault, self.output)

        self.assertFalse((self.output / ".obsidian").exists())

    def test_other_directories_are_copied_as_is(self):
        (self.vault / "about").mkdir()
        (self.vault / "about" / "about.md").write_text("about me", encoding="utf-8")

        copy_vault_resources(self.vault, self.output)

        self.assertTrue((self.output / "about" / "about.md").exists())


if __name__ == '__main__':
    unittest.main()
