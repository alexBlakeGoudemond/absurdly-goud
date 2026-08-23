CI: Convert, Build, Deploy (GitHub Pages)

This repository treats the Obsidian vault (absurdly-goud-obsidian) as the single source of truth. The GitHub Actions
workflow at `.github/workflows/convert-build-deploy.yml` does the following on pushes to `main` (or manual dispatch):

- Runs the Obsidian -> Jekyll converter:
  `python scripts/obsidian_to_jekyll.py --vault absurdly-goud-obsidian --out-dir site_src`
- Installs Ruby gems with Bundler and builds the site from `site_src` using Jekyll
- Uploads the generated `site/` and deploys via GitHub Pages

Notes:

- Do NOT commit generated `site_src/` or `site/` — the workflow generates them in CI.
- If you need pagination or other site behavior changes, update `_config.yml` and templates, and verify locally before
  pushing.

Local testing:

- python scripts/obsidian_to_jekyll.py
- bundle install
- bundle exec jekyll build --source site_src --destination site

If you want a different publish strategy (commit generated site_src, or publish gh-pages branch), say so and I can add
an alternate workflow.