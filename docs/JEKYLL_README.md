# Jekyll README

## Jekyll Use Case

Jekyll takes Markdown, HTML, and templates and generates a static website.

GitHub Pages has built-in support for Jekyll.

A Jekyll site can look like this:

```text
absurdly-goud/
├── _config.yml
├── _layouts/
│   └── default.html
├── index.md
├── about.md
└── ...
```

Jekyll turns the source files into a static website:

```text
Source
  │
  ▼
Jekyll
  │
  ▼
_site/
  ├── index.html
  ├── about.html
  └── ...
```

## Jekyll Setup

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

## Jekyll Files Explained

### `_config.yml`

Site-wide configuration for Jekyll.

It describes things that apply to the website as a whole:

```text
_config.yml
     │
     ├── Site identity
     ├── Build configuration
     ├── Plugins
     └── Custom variables
              │
              ▼
          Jekyll
              │
              ▼
       generated pages
```

### `_layouts/`

Contains templates used by pages.

For example:

```text
_layouts/
└── default.html
```

A page can use a layout through front matter:

```yaml
---
layout: default
title: About
---
```

The layout can insert the page's content using:

```liquid
{{ content }}
```

This allows multiple pages to share the same HTML structure.

### `index.md`

The homepage content.

It can use a layout:

```yaml
---
layout: default
title: Home
---
```

### `about.md`

A separate page.

It can use the same layout:

```yaml
---
layout: default
title: About
---
```

Jekyll generates the pages into `_site/`.

### `_site/`

Jekyll's generated website.

```text
_site/
├── index.html
├── about.html
└── ...
```

`_site/` is generated output and should **not** be committed to Git.