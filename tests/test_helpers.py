from pathlib import Path

from scripts.obsidian_to_jekyll import (
    ObsidianToJekyllConverter,
)


def make_converter(tmp_path: Path) -> ObsidianToJekyllConverter:
    vault = tmp_path / "vault"
    output = tmp_path / "output"
    source = tmp_path / "source"
    vault.mkdir()
    output.mkdir()
    source.mkdir()
    return ObsidianToJekyllConverter(vault, output, source)
