Obsidian has [callouts](https://obsidian.md/help/callouts) notation which are the same as Markdown Blockquotes. Below are examples of the other kinds of Markdown that should be supported inside of them

> [!note]
> This has a 'note' Style

> [!note]
> This has a wikilink to another note: [[2026-09-03 DUCKS DUCKS DUCKS]]

> [!note]
> This has an embdedded image (should show as inline image): ![[free-real-estate.gif]]

>[!Note]
>This has a image on its own line (should show as figure):
>![[this-is-fine-fire.gif]]

Also - something I have not tested yet are tables:

| Heading 1 | Heading 2 |
| --------- | --------- |
| Content 1 | Content 2 |
and in a callout:

> [!Note]
> | Heading 1 | Heading 2|
> |---|---|
> | Content 1 | Content 2|

