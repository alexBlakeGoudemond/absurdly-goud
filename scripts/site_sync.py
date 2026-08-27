#!/usr/bin/env python3
"""
Generic manifest-driven copy engine: syncs individual files or whole trees
from a source location to a destination location, using a content-hash
manifest to skip unchanged files and prune destination output whose source
has vanished. Knows nothing about Obsidian or Jekyll — it's just "keep dest
in sync with source, cheaply, across repeat runs."
"""

import shutil
from pathlib import Path
from typing import Callable

from scripts.website_manifest import sha256, create_manifest_entry, load_manifest, save_manifest


class SiteSync:
    """Tracks a single sync 'run' against one manifest file: which files were
    actually copied this run (`changed_dest_paths`), and the new manifest to
    persist once the run completes."""

    def __init__(self, manifest_path: Path):
        self.manifest_path = manifest_path
        self.old_manifest: dict = {}
        self.new_manifest: dict = {}
        self.changed_dest_paths: list[Path] = []

    def begin_run(self) -> None:
        """Load the on-disk manifest and reset per-run tracking state.
        Call at the start of a run, or reuse directly in tests to simulate a
        second, separate invocation of the sync."""
        self.old_manifest = load_manifest(self.manifest_path)
        self.new_manifest = {}
        self.changed_dest_paths = []

    def save(self) -> None:
        """Persist this run's manifest to disk, so the next run can diff against it."""
        save_manifest(self.manifest_path, self.new_manifest)

    def sync_file(self, source_path: Path, dest_path: Path) -> None:
        """Copy source_path to dest_path only if content changed since last run.
        Manifest is keyed by SOURCE path so renames (same source, new dest) are detectable."""
        source_key = str(source_path)
        current_hash = sha256(source_path)
        old_entry = self.old_manifest.get(source_key)

        # has a rename/move occurred?
        if old_entry and old_entry["dest"] != str(dest_path):
            stale_path = Path(old_entry["dest"])
            if stale_path.exists():
                print(f"Removing stale (renamed) file: '{stale_path}'")
                stale_path.unlink()
            old_entry = None

        # are the contents unchanged?
        if old_entry and old_entry["sha256"] == current_hash and dest_path.exists():
            self.new_manifest[source_key] = old_entry
            return

        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, dest_path)
        print(f"Synced (changed): '{source_path}' -> '{dest_path}'")
        self.new_manifest[source_key] = create_manifest_entry(source_path, dest_path)
        self.changed_dest_paths.append(dest_path)

    def sync_tree(self,
                  source_dir: Path,
                  dest_dir: Path,
                  exclude_suffixes: set[str] = frozenset(),
                  dest_filename: Callable[[str], str] = lambda name: name) -> None:
        """Walk source_dir recursively, syncing each file individually.

        `dest_filename` optionally transforms each file's basename (not its
        full path) before it's joined onto dest_dir — e.g. slugifying a
        free-form title into a URL/Jekyll-safe filename — while the
        directory structure underneath dest_dir is preserved as-is. Left
        untouched by default. SiteSync doesn't care what the transform does;
        that's the caller's business."""
        for source_path in source_dir.rglob("*"):
            if source_path.is_dir():
                continue
            if source_path.suffix.lower() in exclude_suffixes:
                continue
            relative_dir = source_path.relative_to(source_dir).parent
            dest_path = dest_dir / relative_dir / dest_filename(source_path.name)
            self.sync_file(source_path, dest_path)

    def prune_stale_files(self) -> None:
        """Delete any output file whose source no longer exists in the new manifest."""
        stale_keys = self.old_manifest.keys() - self.new_manifest.keys()
        for source_key in stale_keys:
            stale_path = Path(self.old_manifest[source_key]["dest"])
            if stale_path.exists():
                print(f"Removing stale file: '{stale_path}'")
                stale_path.unlink()
