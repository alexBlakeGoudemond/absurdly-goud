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

def register_synced_file(converter: ObsidianToJekyllConverter, dest: Path,
                         last_published: str = "2026-08-29 12:00") -> None:
    """Simulates what a real SiteSync.sync_file call would have populated
    (changed_dest_paths + a matching new_manifest entry) — these tests write
    directly to dest and set changed_dest_paths by hand, bypassing sync_file,
    so last_published_by_dest's lookup needs a manifest entry to match."""
    converter.site_sync.changed_dest_paths.append(dest)
    converter.site_sync.new_manifest[str(dest)] = {
        "source": str(dest),
        "dest": str(dest),
        "sha256": "test-hash",
        "last_published": last_published,
    }