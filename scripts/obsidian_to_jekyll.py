#!/usr/bin/env python3

import argparse
from pathlib import Path
import shutil


def main():
    p = argparse.ArgumentParser(
        description='Export Obsidian vault to a Jekyll-friendly source tree and write into repo or output dir')
    p.add_argument('--vault', default='absurdly-goud-obsidian')
    p.add_argument('--out-root', default='.')
    p.add_argument('--out', default='site_src',
                   help='If provided, generate the site source into this directory and do NOT sync into the repo')
    args = p.parse_args()

    vault = Path(args.vault)
    repo_root = Path(args.out_root)
    out_dir = args.out

    if not vault.exists():
        print(f'Vault path {vault} does not exist. Nothing to do.')
        return

    repo_root = Path(__file__).resolve().parents[1] if repo_root == Path('.') else repo_root

    out = Path(out_dir)
    if out.exists():
        shutil.rmtree(out)

    def ignore_fn(directory, names):
        ignored = set()
        for n in names:
            if n in ['.obsidian', '.git', '.ai-playbook']:
                ignored.add(n)
        return ignored

    shutil.copytree(vault, out, ignore=ignore_fn)

if __name__ == '__main__':
    main()