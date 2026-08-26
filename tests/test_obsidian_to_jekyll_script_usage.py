import argparse
import unittest
from pathlib import Path

from scripts import obsidian_to_jekyll
from scripts.obsidian_to_jekyll import (
    extract_command_line_arguments,
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


if __name__ == '__main__':
    unittest.main()
