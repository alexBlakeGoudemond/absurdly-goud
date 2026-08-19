# Jekyll README

Jekyll takes source content and templates and generates a static website into [`/_site`](#_site).

## Jekyll Use Case

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
_site/
  ├── index.html
  ├── about/
  │   └── index.html
  ├── posts/
  │   └── index.html
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
     ├── Pagination
     ├── Excerpt configuration
     └── Custom variables
              │
              ▼
          Jekyll
              │
              ▼
       generated pages
```

For example, this project uses:

```yaml
permalink: /:year/:month/:day/:title/

excerpt_separator: <!--more-->

paginate: 10
paginate_path: "/posts/page:num/"
```

### `/_includes/`

Contains reusable HTML/Liquid fragments.

For example:

```text
_includes/
├── header.html
└── image.html
```

The shared site header is included by the default layout:

```liquid
{% include header.html %}
```

This means the navigation only needs to be defined in one place.

The image include provides a convenient way to generate predictable post image URLs:

```liquid
{% include image.html
   src="pagination-test-screenshot.png"
   alt="Screenshot showing the pagination test"
%}
```

### `/_layouts/`

Contains templates used by pages and posts.

For example:

```text
_layouts/
├── default.html
└── post.html
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

#### Layout inheritance

The `post` layout uses the `default` layout:

```yaml
---
layout: default
---
```

This means posts automatically inherit the site's document structure and shared header.

The relationship is:

```text
post.md
   │
   ▼
post.html
   │
   ▼
default.html
   │
   ├── header.html
   └── {{ content }}
```

### `/_posts/`

Contains blog posts recognised by Jekyll's built-in `posts` collection.

Posts use a date-based filename:

```text
_posts/
└── 2026-08-19-hello-world.md
```

Jekyll makes these available through:

```liquid
site.posts
```

`site.posts` is sorted newest → oldest by default.

The filename provides the post's date and helps Jekyll generate its permalink.

For this site, posts are published at:

```text
/2026/08/19/hello-world/
```

A post can use the `post` layout:

```yaml
---
layout: post
title: "Hello World"
date: 2026-08-19
---
```

### `/posts/`

This is the website directory for the post archive.

It is separate from `/_posts/`:

```text
_posts/              ← Jekyll's post collection
└── 2026-08-19-hello-world.md

posts/               ← website page
└── index.html
```

`posts/index.html` displays posts using Jekyll's paginator:

```liquid
{% for post in paginator.posts %}
    ...
{% endfor %}
```

The archive uses Microformats2:

```text
h-feed
└── h-entry
    ├── p-name
    ├── dt-published
    └── p-summary
```

The individual post uses:

```text
h-entry
├── p-name
├── dt-published
└── e-content
```

Pagination is configured in `_config.yml`.

For example:

```yaml
paginate: 10
paginate_path: "/posts/page:num/"
```

This produces pages such as:

```text
/posts/
/posts/page2/
/posts/page3/
```

### Post Excerpts

The post archive displays a short preview using:

```liquid
{{ post.excerpt }}
```

This project uses an explicit excerpt separator:

```yaml
excerpt_separator: <!--more-->
```

A post can therefore define exactly where its preview ends:

```markdown
This is the introduction to my post.

<!--more-->

This is the rest of the post.
```

The archive displays the content before `<!--more-->`, while the individual post displays the complete content.

The archive marks the preview as a Microformats2 `p-summary`:

```html
<div class="p-summary">
    {{ post.excerpt }}
</div>
```

### Post Images

Post images are stored under `media/`, following the same date and slug structure as the post:

```text
_posts/
└── 2026-08-19-pagination-test.md

media/
└── 2026/
    └── 08/
        └── 19/
            └── pagination-test/
                └── pagination-test-screenshot.png
```

This gives each post a predictable media directory:

```text
/media/2026/08/19/pagination-test/
```

The project uses `_includes/image.html` to generate the image URL automatically:

```html
<img class="u-photo" src="/media/{{ page.date | date: '%Y/%m/%d' }}/{{ page.slug }}/{{ include.src }}" alt="{{ include.alt }}">
```

A post can then include an image without repeating its date and slug:

```liquid
{% include image.html
   src="pagination-test-screenshot.png"
   alt="Screenshot showing the pagination test"
%}
```

Jekyll generates the final image URL from the post's date, slug, and image filename.

The `u-photo` class marks the image as a Microformats2 photo belonging to the post's `h-entry`.

### `index.md`

The homepage content.

It can use a layout:

```yaml
---
layout: default
title: Home
---
```

### `/about/`

A separate directory containing the About page.

It can use the same layout:

```yaml
---
layout: default
title: About
permalink: /about/
---
```

The source:

```text
about/
└── index.md
```

generates:

```text
_site/
└── about/
    └── index.html
```

### `_site/`

Jekyll's generated website.

For example:

```text
_site/
├── index.html
├── about/
│   └── index.html
├── posts/
│   ├── index.html
│   └── page2/
│       └── index.html
├── 2026/
│   └── 08/
│       └── 19/
│           ├── hello-world/
│           │   └── index.html
│           └── pagination-test/
│               └── index.html
└── media/
    └── ...
```

`_site/` is generated output and should **not** be committed to Git.

It can be safely deleted and regenerated by Jekyll.