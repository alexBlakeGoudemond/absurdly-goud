# How does this website work?

This site uses [Jekyll](https://jekyllrb.com/) to produce a ready-to-serve static website. It does this by taking Markdown and HTML, alongside templates to package the resources into a `site` directory (browser-ready HTML) Jekyll uses [kramdown](https://kramdown.gettalong.org/quickref.html) as its default Markdown Processor

On-top of this - this website uses [Obsidian](https://obsidian.md/) to produce and easily maintain notes. To get this working with Jekyll, some python scripts and GitHub Actions are used.

```
┌──────────────────────┐   ┌──────────────────────┐
│   Jekyll Resources   │   │    Obsidian Vault    │
│                      │   │                      │
│ _layouts / _data /   │   │ notes / posts /      │
│ _includes / css / ...│   │ projects / etc.      │
└──────────┬───────────┘   └──────────┬───────────┘
           │                          │
           │──────────────────────────┘
           │
           │ python script generates the 
           │ 'source files' for the static website
           │
           ↓
┌──────────────────────┐
│      site_src        │
│                      │
│ Jekyll-ready content │
└──────────┬───────────┘
           │ used as 'input' for Jekyll
           ↓
        Jekyll
           │ generates 'output'
           ↓
┌──────────────────────┐
│        _site         │
│                      │
│     static html      │
└──────────┬───────────┘
           │ 
           ↓
      GitHub Pages
```

## Jekyll Overview

> Below is a high level overview of this tool, as well as a condensed cheat sheet for myself when I am working on upgrades!

Jekyll supports [Liquid](https://shopify.dev/docs/api/liquid) as well as other helpful structures (for example [SASS](https://jekyllrb.com/docs/step-by-step/07-assets/#sass))

Jekyll requires the resources in a specific format:
- `_config.yml`
- [Pages](https://jekyllrb.com/docs/pages/) ; standalone files
- [Posts](https://jekyllrb.com/docs/posts/) ; blog files
- [Drafts](https://jekyllrb.com/docs/posts/#drafts) ; unpublished posts
- [Layout Files](https://jekyllrb.com/docs/step-by-step/08-blogging/#layout) ; template to be reused
- [Data Files](https://jekyllrb.com/docs/datafiles/) ; data stored as YAML
- [Includes Files](https://jekyllrb.com/docs/liquid/tags/#includes) ; fragment to be reused as an atomic item

Also, posts support Front Matter; which can use the following key-value properties:
- `layout` ; use this layout
- `permalink` ;  custom defined URL structure
- `published` ; boolean controlling if post shows when `site` is generated
- `<customVariables>` ; to be used in Liquid Syntax
- `<preDefinedVariables>` ;  ready-to-use variables
	- `date` ;  override date from name of the post
	- `category` / `categories` ; place notes in specific directories
	- `tags` ; sticker collecting posts
- `category` / `categories` ;  collect posts into a directory
- `tag` / `tags` ; stickers attached to posts to categorize them

Note that site-design concepts can also be used with Jekyll and Liquid, controlled by CSS
- `sidebar`
- `navbar`
- `header`
- `footer`
- `hamburger menu`
- `breadcrumbs`

> [!Important]
> Front Matter `tags` and `categories` are part of Jekyll's posts system and so the Liquid variables `{{ site.tags.about }}` may not contain the about.md page

> [!Note] Helpful Insights 
> [Front Matter Defaults](https://jekyllrb.com/docs/configuration/front-matter-defaults/) can also be setup in `_config.yaml`
> `Front Matter Tags` can build up an index across your site
> [Front Matter Categories](https://jekyllrb.com/docs/posts/#categories)  group posts together
> [Collections](https://jekyllrb.com/docs/step-by-step/09-collections/) allow grouping anything together, instead of just bundling posts with `categories`

## GitHub Pages

GitHub Pages is GitHub's static website hosting service. It takes static files such as HTML, CSS, JavaScript, and images and makes them available as a website.

GitHub Pages can be configured to publish the contents of a specific **branch** and directory. A branch called `gh-pages` is commonly used for this purpose, but `gh-pages` is **not** a special GitHub Pages feature. It is simply a normal Git branch that we have configured GitHub Pages to publish.

GitHub Actions allows us to execute code on a GitHub-hosted virtual machine. This lets us automate tasks such as converting content, building Jekyll, and deploying the resulting files.

GitHub-hosted runners are provided by GitHub and consume **GitHub Actions minutes** from the account's included usage/quota. 

> [!Important] 
> GitHub Pages are free for public repositories. In this way, I am not paying for hosting!

## Having Notes in Obsidian Vault

I want to be able to easily produce content, and have the infrastructure just work around me. To achieve this - I created an obsidian vault which contains the notes themselves. Jekyll doesn't understand this structure, so I use scripts to convert the content into a structure Jekyll does understand before it runs.

This script runs when I test locally via docker as well as in GitHub Actions for the publication to the site. It produces a directory `site_src`. Jekyll is then told to use that generated directory to prepare the `site` directory as per normal

> [!Important]
> A community plugin for Excalidraw is being used in this obsidian vault. A setting to export the changes to an SVG is also turned on - which allows the SVG to be used in the website generation

