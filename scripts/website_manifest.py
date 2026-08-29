#!/usr/bin/env python3

import hashlib
import json
from pathlib import Path
from datetime import date


def sha256(file_path):
    """Compute the SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read and update hash string value in blocks of 4K
        block_size = 4096
        for byte_block in iter(lambda: f.read(block_size), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def create_manifest_entry(source_path: Path, dest_path: Path) -> dict:
    """Create a manifest entry recording source, dest, content hash, and
    the date this content was last published (i.e. last time its hash
    changed and it was re-synced)."""
    return {
        "source": str(source_path),
        "dest": str(dest_path),
        "sha256": sha256(source_path),
        "last_published": date.today().isoformat(),
    }


def load_manifest(manifest_path: Path) -> dict:
    """Load a manifest from disk, or return empty dict if missing/corrupt."""
    if not manifest_path.exists():
        return {}
    try:
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        print(f"Warning: manifest at '{manifest_path}' is corrupt, ignoring.")
        return {}


def save_manifest(manifest_path: Path, manifest: dict) -> None:
    """Write manifest atomically (temp file + rename) to avoid partial writes."""
    tmp_path = manifest_path.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    tmp_path.replace(manifest_path)
