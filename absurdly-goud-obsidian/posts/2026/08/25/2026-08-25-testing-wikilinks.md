# Testing Wikilinks

In Obsidian I am using wikilinks like this `[[...]]` and it should now just work with Jekyll due to the conversion script!

If I have a wikilink like this:
```markdown
[[Note#Sub Section|Alt Text]]
```
Then the script should convert it into a form that Jekyll requires -  a redirect syntax called a link like this: 
```markdown
[Alt Text]({% link path/to/Note.md %}#sub-section)
```

Testing between posts - this should link [[2026-08-24-aside-and-buttons]]

Testing between posts and about - this should link [[about#AI Usage|AI Usage]]

Testing hyperlinks: [Jekyll](https://jekyllrb.com/)