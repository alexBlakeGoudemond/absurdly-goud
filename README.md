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

Notes on generated fragments
- The converter generates `_includes/home_fragment.md` and `_includes/about_fragment.md` from the
  vault. You can delete the checked-in copies — the converter/watcher will recreate them locally.
- For CI / GitHub Pages: either commit generated files, or add a CI step to run the converter before
  building/publishing, otherwise the site build will miss generated content.

Do not edit generated includes by hand; edit the vault instead.

## Code Entrypoint

This codebase works with Obsidian, Jekyll and GitHub Pages. Python scripts have been set up to assemble the resources
needed by Jekyll in advance. The entrypoint of those scripts is [obsidian_to_jekyll.py](scripts/obsidian_to_jekyll.py)
