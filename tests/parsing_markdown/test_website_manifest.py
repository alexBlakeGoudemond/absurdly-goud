import json
import tempfile
import unittest
from pathlib import Path

from scripts.parsing_markdown.website_manifest import (
    sha256,
    create_manifest_entry,
    load_manifest,
    save_manifest
)


class ManifestCreation(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)
        self.tmp_path = Path(self.tmp_dir.name)

    def test_can_calculate_sha256_of_file(self):
        test_file = self.tmp_path / "test.txt"
        test_file.write_text("Hello, World!", encoding="utf-8")

        expected_hash = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        calculated_hash = sha256(test_file)

        self.assertEqual(calculated_hash, expected_hash)

    def test_renaming_file_does_not_change_sha256(self):
        test_file = self.tmp_path / "test.txt"
        test_file.write_text("Hello, World!", encoding="utf-8")

        original_hash = sha256(test_file)

        new_location = self.tmp_path / "renamed_test.txt"
        test_file.rename(new_location)

        renamed_hash = sha256(new_location)

        self.assertEqual(original_hash, renamed_hash)

    def test_modifying_file_changes_sha256(self):
        test_file = self.tmp_path / "test.txt"
        test_file.write_text("Hello, World!", encoding="utf-8")

        original_hash = sha256(test_file)

        test_file.write_text("Hello, Universe!", encoding="utf-8")

        modified_hash = sha256(test_file)

        self.assertNotEqual(original_hash, modified_hash)

    def test_hashing_missing_file_raises_file_not_found(self):
        # Documents current behaviour: sha256 does not swallow a missing
        # source file, it propagates FileNotFoundError from open(). Callers
        # syncing a file that vanished mid-run should expect this to raise.
        missing_file = self.tmp_path / "does_not_exist.txt"

        with self.assertRaises(FileNotFoundError):
            sha256(missing_file)

    def test_creating_manifest_entry_should_return_correct_structure(self):
        test_file = self.tmp_path / "test.txt"
        test_file.write_text("Hello, World!", encoding="utf-8")

        manifest_entry = create_manifest_entry(test_file, test_file)

        self.assertIn("source", manifest_entry)
        self.assertIn("dest", manifest_entry)
        self.assertIn("sha256", manifest_entry)


class TestLoadManifest(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)
        self.tmp_path = Path(self.tmp_dir.name)

    def test_returns_empty_dict_when_file_missing(self):
        manifest_path = self.tmp_path / "does_not_exist.json"

        result = load_manifest(manifest_path)

        self.assertEqual(result, {})

    def test_loads_valid_manifest_from_disk(self):
        manifest_path = self.tmp_path / "manifest.json"
        data = {"vault/home.md": {"dest": "vision.md", "sha256": "abc123"}}
        manifest_path.write_text(json.dumps(data), encoding="utf-8")

        result = load_manifest(manifest_path)

        self.assertEqual(result, data)

    def test_returns_empty_dict_when_file_is_corrupt(self):
        manifest_path = self.tmp_path / "manifest.json"
        manifest_path.write_text("{ this is not valid json ]", encoding="utf-8")

        result = load_manifest(manifest_path)

        self.assertEqual(result, {})

    def test_returns_empty_dict_when_file_is_empty(self):
        manifest_path = self.tmp_path / "manifest.json"
        manifest_path.write_text("", encoding="utf-8")

        result = load_manifest(manifest_path)

        self.assertEqual(result, {})


class TestSaveManifest(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)
        self.tmp_path = Path(self.tmp_dir.name)

    def test_writes_manifest_to_disk(self):
        manifest_path = self.tmp_path / "manifest.json"
        data = {"vault/home.md": {"dest": "vision.md", "sha256": "abc123"}}

        save_manifest(manifest_path, data)

        self.assertTrue(manifest_path.exists())
        self.assertEqual(json.loads(manifest_path.read_text(encoding="utf-8")), data)

    def test_overwrites_existing_manifest(self):
        manifest_path = self.tmp_path / "manifest.json"
        manifest_path.write_text(json.dumps({"old": "data"}), encoding="utf-8")
        new_data = {"new": "data"}

        save_manifest(manifest_path, new_data)

        self.assertEqual(json.loads(manifest_path.read_text(encoding="utf-8")), new_data)

    def test_no_leftover_temp_file_after_save(self):
        manifest_path = self.tmp_path / "manifest.json"

        save_manifest(manifest_path, {"a": "b"})

        tmp_path = manifest_path.with_suffix(".tmp")
        self.assertFalse(tmp_path.exists())

    def test_round_trip_through_load_manifest(self):
        manifest_path = self.tmp_path / "manifest.json"
        data = {"vault/about.md": {"dest": "about.md", "sha256": "deadbeef"}}

        save_manifest(manifest_path, data)
        result = load_manifest(manifest_path)

        self.assertEqual(result, data)

    def test_can_save_empty_manifest(self):
        manifest_path = self.tmp_path / "manifest.json"

        save_manifest(manifest_path, {})

        self.assertEqual(json.loads(manifest_path.read_text(encoding="utf-8")), {})


if __name__ == '__main__':
    unittest.main()
