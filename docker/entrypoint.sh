#!/usr/bin/env bash
set -euo pipefail

# Entrypoint: convert vault -> site_src, build site, then serve with livereload
# This script runs inside the jekyll container where /site is the repo root (mounted).

echo "Running Obsidian -> Jekyll converter..."
python3 scripts/obsidian_to_jekyll.py --vault absurdly-goud-obsidian --out /site/site_src || true

echo "Building site (one-off)..."
bundle exec jekyll build --source /site/site_src --config /site/_config.yml --destination /site/site || true

echo "Starting jekyll serve (foreground)..."
exec bundle exec jekyll serve --source /site/site_src --config /site/_config.yml --destination /site/site --host 0.0.0.0 --livereload
