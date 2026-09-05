#!/usr/bin/env bash
set -euo pipefail

echo "Running Obsidian -> Jekyll converter..."
python3 -m scripts.obsidian_to_jekyll --vault /workbench/absurdly-goud-obsidian --out-dir /workbench/site_src

echo ""
echo "Checking if syntax highlighting CSS exists"
if [ ! -f /workbench/site_src/assets/css/syntax-highlighting.css ]; then
  echo "Generating syntax highlighting CSS via Rouge..."
  bundle exec rougify style monokai.sublime > /workbench/site_src/assets/css/syntax-highlighting.css
else
  echo "syntax-highlighting.css already exists, skipping generation"
fi

echo ""
echo "Building site (one-off)..."
bundle exec jekyll build --source /workbench/site_src --config /workbench/_config.yml --destination /workbench/_site

echo ""
echo "Starting jekyll serve (foreground)..."
exec bundle exec jekyll serve --source /workbench/site_src --config /workbench/_config.yml --destination /workbench/_site --host 0.0.0.0 --livereload