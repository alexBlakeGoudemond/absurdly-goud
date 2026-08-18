# Jekyll README

## Jekyll Usecase

Jekyll takes Markdown/HTML/templates and generates a static website, and GitHub Pages has first-class Jekyll support

A repository structure like this:

```bash
_posts/
    2026-08-18-my-first-post.md

_pages/
    about.md
    now.md
    projects.md

_layouts/
    default.html
    post.html

_includes/
    header.html
    footer.html

assets/
    css/
    images/

_config.yml
```

... through Jekyll will become a website like this:

```bash
absurdlygoud.com/
├── /
├── /about/
├── /now/
├── /projects/
├── /2026/08/18/my-first-post/
└── ...
```

## Jekyll Setup

Jekyll has two separate jobs

```bash
                    Jekyll
                      │
            ┌─────────┴─────────┐
            │                   │
       Build the site       Run locally
            │                   │
            ▼                   ▼
     GitHub Pages          Ruby + Jekyll
```

GitHub Pages can build Jekyll sites for you remotely. Ruby isn't required just to have a Jekyll-powered GitHub Pages
website. However installing it is recommended as it helps with local development and debugging.
