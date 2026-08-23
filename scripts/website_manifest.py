#!/usr/bin/env python3

import hashlib

from pathlib import Path


def sha256(file_path):
    """Compute the SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read and update hash string value in blocks of 4K
        block_size = 4096
        for byte_block in iter(lambda: f.read(block_size), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def create_manifest_entry(file_path: Path) -> dict:
    """Create a manifest entry for a given file."""
    file_hash = sha256(file_path)
    return {
        "location": str(file_path),
        "sha256": file_hash
    }
