import unittest
import tempfile
from pathlib import Path

from scripts.parsing_markdown.site_sync import SiteSync


def make_site_sync(tmp_path: Path) -> SiteSync:
    manifest_path = tmp_path / ".manifest.json"
    sync = SiteSync(manifest_path)
    sync.begin_run()
    return sync


def start_next_run(sync: SiteSync) -> None:
    """Persist whatever this run produced, then begin a fresh run —
    mirrors exactly what a second real invocation would see."""
    sync.save()
    sync.begin_run()


class TestSyncFile(unittest.TestCase):
    """Covers first-time setup, recurring/unchanged, recurring/changed, and rename cases."""

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)
        self.tmp_path = Path(self.tmp_dir.name)
        self.sync = make_site_sync(self.tmp_path)

    def test_new_file_is_copied_and_recorded(self):
        source = self.tmp_path / "note.md"
        source.write_text("hello", encoding="utf-8")
        dest = self.tmp_path / "out" / "note.md"

        self.sync.sync_file(source, dest)

        self.assertTrue(dest.exists())
        self.assertEqual(dest.read_text(encoding="utf-8"), "hello")
        self.assertIn(dest, self.sync.changed_dest_paths)
        self.assertIn(str(source), self.sync.new_manifest)

    def test_unchanged_file_is_skipped_on_recurring_run(self):
        source = self.tmp_path / "note.md"
        source.write_text("hello", encoding="utf-8")
        dest = self.tmp_path / "out" / "note.md"
        self.sync.sync_file(source, dest)  # first-time setup

        start_next_run(self.sync)  # recurring setup
        self.sync.sync_file(source, dest)

        self.assertEqual(self.sync.changed_dest_paths, [])

    def test_changed_file_is_recopied_on_recurring_run(self):
        source = self.tmp_path / "note.md"
        source.write_text("hello", encoding="utf-8")
        dest = self.tmp_path / "out" / "note.md"
        self.sync.sync_file(source, dest)

        start_next_run(self.sync)
        source.write_text("updated", encoding="utf-8")
        self.sync.sync_file(source, dest)

        self.assertEqual(dest.read_text(encoding="utf-8"), "updated")
        self.assertIn(dest, self.sync.changed_dest_paths)

    def test_renamed_source_removes_old_dest_on_recurring_run(self):
        source = self.tmp_path / "note.md"
        source.write_text("hello", encoding="utf-8")
        old_dest = self.tmp_path / "out" / "old_location.md"
        self.sync.sync_file(source, old_dest)

        start_next_run(self.sync)
        new_dest = self.tmp_path / "out" / "new_location.md"
        self.sync.sync_file(source, new_dest)

        self.assertFalse(old_dest.exists())
        self.assertTrue(new_dest.exists())


class TestSyncTree(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)
        self.tmp_path = Path(self.tmp_dir.name)
        self.sync = make_site_sync(self.tmp_path)

    def test_no_exclusions_by_default(self):
        source_dir = self.tmp_path / "src"
        source_dir.mkdir()
        (source_dir / "image.png").write_bytes(b"bytes")
        dest_dir = self.tmp_path / "dest"

        self.sync.sync_tree(source_dir, dest_dir)

        self.assertTrue((dest_dir / "image.png").exists())

    def test_excluded_suffix_is_skipped(self):
        source_dir = self.tmp_path / "src"
        source_dir.mkdir()
        (source_dir / "image.png").write_bytes(b"bytes")
        (source_dir / "notes.md").write_text("hi", encoding="utf-8")
        dest_dir = self.tmp_path / "dest"

        self.sync.sync_tree(source_dir, dest_dir, exclude_suffixes={".png"})

        self.assertFalse((dest_dir / "image.png").exists())
        self.assertTrue((dest_dir / "notes.md").exists())

    def test_exclusion_matches_case_insensitively(self):
        source_dir = self.tmp_path / "src"
        source_dir.mkdir()
        (source_dir / "image.PNG").write_bytes(b"bytes")
        dest_dir = self.tmp_path / "dest"

        self.sync.sync_tree(source_dir, dest_dir, exclude_suffixes={".png"})

        self.assertFalse((dest_dir / "image.PNG").exists())

    def test_nested_files_are_synced_via_rglob(self):
        source_dir = self.tmp_path / "src"
        nested = source_dir / "a" / "b"
        nested.mkdir(parents=True)
        (nested / "deep.md").write_text("hi", encoding="utf-8")
        dest_dir = self.tmp_path / "dest"

        self.sync.sync_tree(source_dir, dest_dir)

        self.assertTrue((dest_dir / "a" / "b" / "deep.md").exists())

    def test_dest_filename_transform_renames_on_the_way_out(self):
        source_dir = self.tmp_path / "src"
        source_dir.mkdir()
        (source_dir / "My Note.md").write_text("hi", encoding="utf-8")
        dest_dir = self.tmp_path / "dest"

        self.sync.sync_tree(source_dir, dest_dir, dest_filename=lambda name: name.lower().replace(" ", "-"))

        self.assertTrue((dest_dir / "my-note.md").exists())
        self.assertFalse((dest_dir / "My Note.md").exists())

    def test_dest_filename_transform_preserves_directory_structure(self):
        source_dir = self.tmp_path / "src"
        nested = source_dir / "sub folder"
        nested.mkdir(parents=True)
        (nested / "My Note.md").write_text("hi", encoding="utf-8")
        dest_dir = self.tmp_path / "dest"

        self.sync.sync_tree(source_dir, dest_dir, dest_filename=lambda name: name.lower().replace(" ", "-"))

        # only the FILENAME is transformed — the folder name is left as-is
        self.assertTrue((dest_dir / "sub folder" / "my-note.md").exists())

    def test_dest_filename_transform_is_identity_by_default(self):
        source_dir = self.tmp_path / "src"
        source_dir.mkdir()
        (source_dir / "My Note.md").write_text("hi", encoding="utf-8")
        dest_dir = self.tmp_path / "dest"

        self.sync.sync_tree(source_dir, dest_dir)

        self.assertTrue((dest_dir / "My Note.md").exists())


class TestPruneStaleFiles(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)
        self.tmp_path = Path(self.tmp_dir.name)
        self.sync = make_site_sync(self.tmp_path)

    def test_deletes_output_for_source_removed_on_recurring_run(self):
        source = self.tmp_path / "gone.md"
        source.write_text("content", encoding="utf-8")
        dest = self.tmp_path / "out" / "gone.md"
        self.sync.sync_file(source, dest)  # first-time setup

        start_next_run(self.sync)  # recurring setup
        source.unlink()  # source no longer present this run — never re-synced
        self.sync.prune_stale_files()

        self.assertFalse(dest.exists())

    def test_keeps_output_still_present_on_recurring_run(self):
        source = self.tmp_path / "kept.md"
        source.write_text("content", encoding="utf-8")
        dest = self.tmp_path / "out" / "kept.md"
        self.sync.sync_file(source, dest)

        start_next_run(self.sync)
        self.sync.sync_file(source, dest)  # still present, re-synced (cache hit)
        self.sync.prune_stale_files()

        self.assertTrue(dest.exists())


if __name__ == '__main__':
    unittest.main()
