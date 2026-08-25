# Testing Wikilinks

In Obsidian I am using wikilinks like this `[[...]]` and it should now just work with Jekyll due to the conversion script!

<!--more-->

If I have a wikilink like this:
```markdown
[[Note#Sub Section|Alt Text]]
```
Then the script should convert it into a form that Jekyll requires -  a redirect syntax called a link like this: 
```markdown
[Alt Text]({% link path/to/Note.md %}#sub-section)
```

Testing between posts - this should link [[2026-08-24-aside-and-buttons]]