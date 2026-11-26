Exploring caching with GitHub Actions further - I went on to add Jekyll's metadata cache (CSS etc). This Github Actions step yielded this result 

![[2026-11-26 Caching Jekyll Metadata.webp]]

Insights:
- Restore Step: runs on startup and tries to find the Jekyll primary key
- Post Restore Jekyll build cache: automatically runs after job; save the cache contents
- `Cache not found` normal on first run
- `Cache hit occurred ... not saving cache` - the cache did not change, nothing to save
- `POST /... / Sent-style logs` come from the GitHub cache service HTTP API
	- First log: cache version accepted and cache uploaded
	- Second log: hit and download
	- Third log: hit, but no upload because the primary key already matched
	- FYI: `21757952 of 32506581` is a fraction of the progress bar - hence `66.9%`


> [!important]
> However - this currently does not load the templates like `_include` ![[this-is-fine-fire.gif]] Meaning the site doesnt load - just the background... So I chose to remove the `-incremental` flag. This means we are not actually taking advantage of the caching - but will keep it in anyway!

