When working on something yesterday, I discovered that wikilink URLs that contained a pipe operator were not being parsed by Kramdown correctly. This post acts as a quick test for this

Testing Wikilink URL:
- [Wikilink without pipe](https://blot.im/how/formatting/wikilinks)
- [Wikilink | with pipe](https://blot.im/how/formatting/wikilinks)

Testing Markdown URL:
- [Markdown without pipe](https://blot.im/how/formatting/wikilinks)
- [Markdown | with pipe](https://blot.im/how/formatting/wikilinks)

Related syntax that is not URLs that should still be supported:
- Link to page using Wikilink and spaces in filename: [[2026-08-31 88x31 Exploration|88x31 Exploration]]
- Link to page using Wikilink and dashes in filename: [[2026-08-19-hello-world|Hello World]]