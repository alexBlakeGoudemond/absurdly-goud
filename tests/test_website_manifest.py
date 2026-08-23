import unittest
from pathlib import Path
import tempfile

from scripts.website_manifest import (
    sha256,
    create_manifest_entry
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

    def test_creating_manifest_entry_should_return_correct_structure(self):
        test_file = self.tmp_path / "test.txt"
        test_file.write_text("Hello, World!", encoding="utf-8")

        manifest_entry = create_manifest_entry(test_file)

        self.assertIn("location", manifest_entry)
        self.assertIn("sha256", manifest_entry)


if __name__ == '__main__':
    unittest.main()
