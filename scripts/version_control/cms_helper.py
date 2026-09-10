#!/usr/bin/env python3
"""
Content Management System (CMS) helper functions for the Jekyll site build.
"""

import subprocess
import yaml
from datetime import datetime, timezone

def write_last_updated(repo_path, output_path, recreate_directory=False):
    result = subprocess.run(
        ["git", "-C", repo_path, "log", "-1", "--format=%aI"],  # ISO 8601
        capture_output=True, text=True, check=True
    )
    commit_date = result.stdout.strip()

    data = {
        "last_updated": commit_date,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    if recreate_directory:
        output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False)

def write_last_commit_message(repo_path, output_path, branch="main", recreate_directory=False):
    result = subprocess.run(
        ["git", "-C", repo_path, "log", "-1", "--format=%B", branch],  # subject line only
        capture_output=True, text=True, check=True
    )
    commit_message = result.stdout.strip()

    data = {
        "last_commit_message": commit_message,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    if recreate_directory:
        output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False)