# Jekyll

What Jekyll does

- Converts markdown, templates, and assets into `site/` (static output)

## Key Directories

- `_posts/`: blog source (date-slug filenames)
- `_includes/`, `_layouts/`: shared templates
- `posts/`: archive pages using paginator

## Images & media

- `assets/` stores images used by posts and more
- use `_includes/image.html` and `_includes/figure.html` to insert images

## Local test

See [Local Testing](LOCAL_TESTING.md)

## Notes

- `_site/` and `site_src` are generated — don’t commit
- Generated `includes` may be helpful for debugging and CI
- `Liquid` and its syntax is also supported

### Jekyll Use Case

Jekyll takes Markdown, HTML, templates, and other assets and generates a static website.

GitHub Pages has built-in support for Jekyll.

A Jekyll site can look like this:

```text
absurdly-goud/
├── _config.yml
├── _includes/
│   ├── header.html
│   └── image.html
├── _layouts/
│   ├── default.html
│   └── post.html
├── _posts/
│   └── 2026-08-19-hello-world.md
├── posts/
│   └── index.html
├── index.md
├── about/
│   └── index.md
└── ...
```

Jekyll processes the source files into a static website:

```text
Source
  │
  ▼
Jekyll
  │
  ▼
site/
  ├── index.html
  ├── about/
  │   └── index.html
  ├── posts/
  │   └── index.html
  └── ...
```

#### Jekyll Setup

Jekyll has two separate concerns:

```text
                    Jekyll
                      │
            ┌─────────┴─────────┐
            │                   │
       Build the site       Run locally
            │                   │
            ▼                   ▼
      GitHub Pages          Ruby + Jekyll
```

GitHub Pages can build Jekyll sites remotely.

Ruby and Jekyll are therefore not required just to deploy a Jekyll site to GitHub Pages.

Installing them locally is useful for development and testing.

In this project, Ruby and Jekyll run inside Docker.

