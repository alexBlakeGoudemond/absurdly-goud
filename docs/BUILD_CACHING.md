# Build Caching — How It Works & Current Limits

## What is built

[obsidian_to_jekyll.py](../scripts/obsidian_to_jekyll.py) uses a **content-hash manifest** to avoid re-copying unchanged
files on every run.

- [website_manifest.py](../scripts/parsing_markdown/website_manifest.py) hashes each source file (SHA256) and can load/save a manifest
  to/from `site_src/.manifest.json`
- `ObsidianToJekyllConverter.sync_file()` compares each file's current hash against the manifest from the last run:
  - **Unchanged** → skip the copy entirely
  - **Changed** → recopy and re-process (frontmatter, etc.)
  - **New** → copy for the first time
  - **Renamed** (same source, different destination) → delete the old output, write the new one
- Files removed from the vault get pruned from `site_src` automatically
  (`prune_stale_files`)
- The manifest is keyed by **source path**, so renames are detectable without needing to invert the whole manifest

## Where this actually helps

**Local dev loop.** Running the converter repeatedly (e.g. via the file watcher) only touches files that’ve changed
since last time — fast, near-instant rebuilds instead of a full resync on every save.

## Current limit: it does *not* speed up CI

GitHub-hosted Actions runners are **ephemeral** — nothing persists between workflow runs unless explicitly cached.

At this time, every CI run:

1. Does a fresh `git checkout` (no old `site_src/.manifest.json` present)
2. So `old_manifest` is always `{}` → every file shows as "changed" → full resync every time
3. `jekyll build` itself also always does a full build regardless — it has no awareness of the manifest at all

**Net effect:** the manifest exists and gets logged in CI, but it currently provides zero build-time savings there. The
real CI cost is `bundle install` (gems) and `jekyll build`, not the Python conversion step — and gem installs are
already cached via `actions/cache` on `vendor/bundle`.

## If CI caching is wanted later

Would need `actions/cache` wired to persist `site_src/.manifest.json` between runs.

Worth it only if the vault grows large enough that the conversion step becomes a measurable chunk of build time — not
the case at current scale.

Higher-leverage lever for CI minutes: confirm the gem cache is actually hitting
(check Action logs for `Cache restored from key:`).
