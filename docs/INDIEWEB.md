# IndieWeb

The IndieWeb is a community of people building their own websites and web applications, with the goal of reclaiming
ownership of their online presence. The IndieWeb movement emphasizes the importance of personal websites, decentralized
social networking, and open standards.

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

## Domain Architecture

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