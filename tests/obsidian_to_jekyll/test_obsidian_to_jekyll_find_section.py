import unittest
from pathlib import Path

from scripts.obsidian_to_jekyll import (
    find_parent_section,
)


class TestFindSection(unittest.TestCase):

    def test_returns_matching_ancestor_folder(self):
        result = find_parent_section(Path("journey/design/website-design.md"), ["journey"])
        self.assertEqual(result, "journey")

    def test_returns_none_when_no_ancestor_matches(self):
        result = find_parent_section(Path("about.md"), ["journey"])
        self.assertIsNone(result)

    def test_only_matches_configured_folders(self):
        result = find_parent_section(Path("progress/update.md"), ["journey"])
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
