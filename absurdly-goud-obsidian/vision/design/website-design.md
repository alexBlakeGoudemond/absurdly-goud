# How does this website work?

This site uses [Jekyll](https://jekyllrb.com/) to produce a ready-to-serve static website. It does this by taking Markdown and HTML, alongside templates to package the resources into a `site` directory (browser-ready HTML)

On-top of this - this website uses [Obsidian](https://obsidian.md/) to produce and easily maintain notes. To get this working with Jekyll, script and GitHub Actions are used.

## Jekyll Overview

Jekyll supports [Liquid](https://shopify.dev/docs/api/liquid) as well as other helpful structures (for example [SASS](https://jekyllrb.com/docs/step-by-step/07-assets/#sass))

Jekyll requires the resources in a specific format:
- `_config.yml`
- [Pages](https://jekyllrb.com/docs/pages/) ; standalone files
- [Posts](https://jekyllrb.com/docs/posts/) ; blog files
- [Drafts]()
- [Layout Files]()
- [Data Files](https://jekyllrb.com/docs/datafiles/) ; data stored as YAML
- [Includes Files]()

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
> Front Matter `tags` and `categories` are part of its posts system and so the Liquid variables `{{ site.tags.about }}` may not contain the about.md page

> [!Note] Helpful Insights 
> [Front Matter Defaults](https://jekyllrb.com/docs/configuration/front-matter-defaults/) can also be setup in `_config.yaml`
> `Front Matter Tags` can build up an index across your site
> [Front Matter Categories](https://jekyllrb.com/docs/posts/#categories)  group posts together
> [Collections]() allow grouping anything together, instead of just bundling posts with `categories`

## Having Notes in Obsidian Vault

I want to be able to easily produce notes, and have the infrastructure just work around me. To achieve this - I created an obsidian vault which contains the notes themselves. Jekyll doesn't understand this structure, so I use scripts to convert the content into a structure Jekyll does understand before it runs.

This script runs when I test locally via docker as well as in GitHub Actions for the publication to the site. It produces a directory `site_src`. Jekyll is then told to use that generated directory to prepare the `site` directory as per normal