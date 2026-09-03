# AGENTS — AI Quick Onboarding

Repo snapshot

- Jekyll site generated from an Obsidian vault: absurdly-goud-obsidian → site_src → site (published to
  absurdlygoud.com).
- Identity domain: alexblakegoudemond.com (IndieAuth / rel="me").

Key files

- Converter: scripts/obsidian_to_jekyll.py
- Manifest: scripts/parsing_markdown/website_manifest.py
- Docs: docs/, docs/ARCHIVE.md (originals archived)

Quick commands (run from repo root, Windows PowerShell)

- Convert: python scripts/obsidian_to_jekyll.py --vault absurdly-goud-obsidian --out-dir site_src
- Build: bundle install && bundle exec jekyll build --source site_src --destination site

Rules for AI agents

- Prefer minimal, surgical edits; archive replaced long-form docs to docs/ARCHIVE.md.
- Do not commit on behalf of the user unless explicitly allowed; write changes to working tree and show diffs.
- Avoid editing generated output (site/, generated includes) — edit the vault or source files instead.
- Use Windows-style paths and repo-root relative paths in commands.
- When creating commits: include Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com> unless user opts
  out.

Where to look first

- README.md, docs/README.md, docs/JEKYLL_README.md, scripts/, _layouts/, _includes/, _posts/

Contact / origin

- https://github.com/alexBlakeGoudemond
