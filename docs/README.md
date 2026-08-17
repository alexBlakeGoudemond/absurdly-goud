# Documentation README

This repo was initially created as a personal website for Alex Blake-Goudemond, namely as a way to join the Indie Web.

Any relevant details will be documented here.

# Infrastructure

## Overview

The personal website is hosted using GitHub Pages and served through the custom domain `absurdlygoud.com`.

    Internet
        │
        ▼
    ┌─────────────────────┐
    │  absurdlygoud.com   │
    └──────────┬──────────┘
               │
            DNS lookup
               │
               ▼
    ┌─────────────────────┐
    │      GoDaddy        │
    │  Authoritative DNS  │
    └──────────┬──────────┘
               │
               │ `A` records via distinct IP Addresses
               ▼
    ┌─────────────────────┐
    │    GitHub Pages     │
    └──────────┬──────────┘
               │
               ▼
    alexBlakeGoudemond/personal-website
               │
               ▼
           index.html
               │
               ▼
      https://absurdlygoud.com

## Repository

See [Repository](../README.md#Repository)

## DNS

The domain is registered/managed through GoDaddy.

Authoritative nameservers:

```
    ns33.domaincontrol.com
    ns34.domaincontrol.com
```

The apex domain (`@`) points to GitHub Pages using GitHub's recommended A records:

| Type | Name | Data            |
|------|------|-----------------|
| A    | @    | 185.199.108.153 |
| A    | @    | 185.199.109.153 |
| A    | @    | 185.199.110.153 |
| A    | @    | 185.199.111.153 |

The previous GoDaddy Website Builder A record was removed.

## Domain Verification

GitHub domain ownership was verified using a DNS TXT record:

```
_github-pages-challenge-alexBlakeGoudemond.absurdlygoud.com
```

The TXT record should remain in place for GitHub's domain verification.

## HTTPS

GitHub Pages is configured with:

```
    Custom domain: absurdlygoud.com
    DNS check: successful
    Enforce HTTPS: enabled
```

The site is therefore served over:

```
https://absurdlygoud.com
```

## IndieWeb

The website currently contains a `rel="me"` link to the owner's GitHub profile:

```html
    <a href="https://github.com/alexBlakeGoudemond" rel="me">
    github.com/alexBlakeGoudemond
</a>
```

This establishes the intended relationship:

```
    https://absurdlygoud.com
            │
            │ rel="me"
            ▼
    https://github.com/alexBlakeGoudemond
```

This allows validation for this relationship using IndieWebify.me.

## DNS Propagation Note

The authoritative GoDaddy DNS servers and public DNS resolvers have been confirmed to return the GitHub Pages IP
addresses.

For example:

```
    8.8.8.8 (Google DNS)
        → GitHub Pages

    1.1.1.1 (Cloudflare DNS)
        → GitHub Pages
```

The local network router (`192.168.0.1`) temporarily continued returning the old GoDaddy Website Builder addresses due
to DNS caching. This did not affect the public DNS configuration.

The site was successfully verified from a mobile device using mobile data, confirming that the public site resolves
correctly.

# IndieWeb: h-card

A **h-card** is a machine-readable "business card" for a person or organization.

It uses **Microformats** — CSS classes added to normal HTML — to tell software who you are.

```html

<div class="h-card">
    <p class="p-name">Alex Blake-Goudemond</p>

    <a class="u-url" href="https://absurdlygoud.com">
        absurdlygoud.com
    </a>

    <a class="u-url" href="https://github.com/alexBlakeGoudemond" rel="me">
        GitHub
    </a>
</div>
```

## Common properties

- `h-card` → identifies the overall card
- `p-name` → person's name
- `u-url` → URL associated with the person
- `u-photo` → person's photo
- `p-note` → description/note

### Mental model

```text
rel="me"  → "What other websites represent me?"
h-card    → "Who am I?"
```

The goal is for **humans to see a normal webpage while software can understand the identity information**.
