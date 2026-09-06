## Decisions Made
- Route: Python preprocessor detects Obsidian `> [!type]` syntax and rewrites it
  (not manual {% include %} authoring — source stays pure Obsidian markdown)
- Liquid mechanism: Option 1 — {% capture %} + {% include callout.html %} + markdownify
  (rejected Option 3 "raw HTML from Python" because it would need a second markdown
  engine and break images/wikilinks/tables rendering consistently with the rest of site)
  (Option 2 "custom Liquid block tag" kept as a possible future upgrade, not needed now)
- Aliases (tip/hint/important, success/check/done, etc.) resolve to canonical type
  in the PYTHON script, not in Liquid/Jekyll
- Collapsible (+/-) flag: parsed and passed through now, but actual collapse
  behavior (JS/\<details\>) deferred until later
- Nesting callouts inside callouts: explicitly out of scope for now
- CSS and JS: not started yet — deliberately deferred until conversion pipeline
  (Python -> Liquid -> kramdown output) is proven to work smoothly

## Files anticipated to be touched (not all at once)
- [ ] Python script: callout detection/conversion (new or added to existing pipeline)
- [ ] Test script for the callout Python script
- [ ] Jekyll _includes/callout.html
- [ ] Lucide icons (source/storage TBD — inline SVG vs included files)
- [ ] CSS for callout styling (mirroring Obsidian look)
- [ ] JS for collapsible behavior (later)

## Open Questions / To Decide Together
- Execution order across Python scripts — needs review of existing scripts
  (frontmatter, codeblocks, etc.) together to decide where callout pass fits
- Exact Python -> Liquid output contract (capture var naming, include params:
  type, title, collapsible, content)
- Where wikilink resolution happens relative to callout pass (must happen
  BEFORE callout capture/markdownify so callout content is plain markdown by
  the time it's processed)
- Default title per canonical type (e.g. note -> "Note", abstract -> "Abstract")
  — table location TBD (hardcoded in include vs _data/callouts.yml)
- Full obsidian callout type list to support (confirm against Obsidian docs —
  currently missing explicit note/abstract/summary/tldr/quote/cite from list)

## Current Test Findings (from live site test, 2026-09-06)
Working already:
  - normal text in callout
  - wikilinks to other files inside callout
  - inline images inside callout
Not working yet:
  - tables in general (outside callouts too — base site issue)
  - tables inside callouts
  - styling (expected — not started)

## Immediate Next Step
-> Investigate why tables aren't rendering on the site at all (base kramdown/Jekyll
   config issue, likely unrelated to callouts) before testing tables-in-callouts
   specifically, since callout table support depends on base table support existing.