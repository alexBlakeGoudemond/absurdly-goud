# Documentation README

This repo was initially created as a personal website for Alex Blake-Goudemond, namely as a way to join the IndieWeb.

Any relevant details will be documented here.

# Infrastructure

## Overview

The personal website is hosted using GitHub Pages and served through the custom domain `absurdlygoud.com`.

A separate domain, `alexblakegoudemond.com`, acts as the personal identity and IndieAuth domain.

```text
                         Internet
                            │
              ┌─────────────┴─────────────┐
              │                           │
              ▼                           ▼
    ┌─────────────────────┐     ┌──────────────────────────┐
    │  absurdlygoud.com   │     │ alexblakegoudemond.com   │
    │                     │     │                          │
    │   IndieWeb site     │     │ Identity / IndieAuth     │
    └──────────┬──────────┘     └────────────┬─────────────┘
               │                             │
               ▼                             ▼
        GitHub Pages                   GitHub Pages
               │                             │
               ▼                             ▼
    personal-website repo       alexblakegoudemond repo
               │                             │
               ▼                             ▼
          index.html                    index.html
```

### Domain responsibilities

| Domain                   | Responsibility                      |
|--------------------------|-------------------------------------|
| `absurdlygoud.com`       | Actual IndieWeb website and content |
| `alexblakegoudemond.com` | Personal identity and IndieAuth     |

The two domains are connected using Microformats `rel="me"` links.

## Repository

See [Repository](../README.md#Repository)

## DNS

The domain is registered/managed through GoDaddy.

Authoritative nameservers:

```text
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

```text
_github-pages-challenge-alexBlakeGoudemond.absurdlygoud.com
```

The TXT record should remain in place for GitHub's domain verification.

## HTTPS

GitHub Pages is configured with:

```text
Custom domain: absurdlygoud.com
DNS check: successful
Enforce HTTPS: enabled
```

The site is therefore served over:

```text
https://absurdlygoud.com
```

# IndieWeb

## Identity

The personal identity is represented by:

```text
https://alexblakegoudemond.com
```

This domain is separate from the actual IndieWeb site.

The relationship between the two domains is established using reciprocal `rel="me"` links:

```text
    https://alexblakegoudemond.com
                │
                │ rel="me"
                ▼
    https://absurdlygoud.com
```

Both domains also link to the owner's GitHub profile:

```text
https://github.com/alexBlakeGoudemond
```

This establishes the following identity graph:

```text
                 Alex
                  │
       ┌──────────┴──────────┐
       │                     │
       ▼                     ▼
alexblakegoudemond.com   absurdlygoud.com
       │                     │
       │                     │
       └─────────┬───────────┘
                 │
              rel="me"
                 │
                 ▼
    github.com/alexBlakeGoudemond
```

## IndieAuth

`alexblakegoudemond.com` is the IndieAuth identity domain.

Its HTML declares IndieAuth.com's authorization and token endpoints:

```html

<link rel="authorization_endpoint"
      href="https://indieauth.com/auth">

<link rel="token_endpoint"
      href="https://tokens.indieauth.com/token">
```

This allows an IndieWeb client to discover where authentication and token exchange should take place when using
`alexblakegoudemond.com` as the user's identity.

The actual website content remains on:

```text
https://absurdlygoud.com
```

## h-card

A **h-card** is a machine-readable "business card" for a person or organization.

It uses **Microformats** — CSS classes added to normal HTML — to tell software who you are.

The `absurdlygoud.com` site currently exposes:

```html

<div class="h-card">
    <p class="p-name">
        Alex Blake-Goudemond
    </p>

    <a class="u-url"
       href="https://alexblakegoudemond.com"
       rel="me">
        alexblakegoudemond.com
    </a>

    <a class="u-url"
       href="https://absurdlygoud.com">
        absurdlygoud.com
    </a>

    <a class="u-url"
       href="https://github.com/alexBlakeGoudemond"
       rel="me">
        GitHub
    </a>
</div>
```

### Common properties

- `h-card` → identifies the overall card
- `p-name` → person's name
- `u-url` → URL associated with the person
- `u-photo` → person's photo
- `p-note` → description/note
- `rel="me"` → establishes an identity relationship with another URL

### Mental model

```text
h-card    → "Who am I?"
u-url     → "What URLs are associated with me?"
rel="me"  → "This other URL also represents me."
```

The goal is for **humans to see a normal webpage while software can understand the identity information**.

# Domain Architecture

The intended separation is:

```text
alexblakegoudemond.com
    │
    ├── Personal identity
    ├── h-card
    ├── rel="me" → absurdlygoud.com
    ├── rel="me" → GitHub
    ├── IndieAuth authorization endpoint
    └── IndieAuth token endpoint


absurdlygoud.com
    │
    ├── Actual IndieWeb website
    ├── h-card
    ├── rel="me" → alexblakegoudemond.com
    └── rel="me" → GitHub
```

The identity domain and website domain therefore have distinct responsibilities while remaining connected through the
IndieWeb identity graph.