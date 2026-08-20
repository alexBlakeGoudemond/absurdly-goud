# personal-website
Personal website for AlexBlakeGoudemond

For more information, please refer to the [Documentation README](docs/README.md).

## Repository

- **Repository:** `alexBlakeGoudemond/absurdly-goud`
- **Visibility:** Public
- **Hosting:** GitHub Pages
- **Publishing source:** `main` branch, repository root
- **Custom domain:** `absurdlygoud.com`
- **License**: MIT

## Obsidian workflow

This repo treats the Obsidian vault (absurdly-goud-obsidian) as the source of truth. The exporter
scripts/obsidian_to_jekyll.py converts vault content into Jekyll site sources and writes generated
fragments into _includes.

Development helper:
- Ensure Python is available and run (PowerShell from repo root): `.
  scripts\dev.ps1` — it installs watchdog (user), runs the converter once, starts a watcher that
  re-runs the converter on markdown changes, then launches `bundle exec jekyll serve --livereload`.

Notes on generated fragments
- The converter generates `_includes/home_fragment.md` and `_includes/about_fragment.md` from the
  vault. You can delete the checked-in copies — the converter/watcher will recreate them locally.
- For CI / GitHub Pages: either commit generated files, or add a CI step to run the converter before
  building/publishing, otherwise the site build will miss generated content.

Do not edit generated includes by hand; edit the vault instead.