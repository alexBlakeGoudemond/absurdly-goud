# DNS Readme

The domain is registered/managed through GoDaddy.

Authoritative nameservers:

```text
ns33.domaincontrol.com
ns34.domaincontrol.com
```

The apex domain (`@`) points to GitHub Pages using GitHub's recommended `A records`:

| Type | Name | Data            |
|------|------|-----------------|
| A    | @    | 185.199.108.153 |
| A    | @    | 185.199.109.153 |
| A    | @    | 185.199.110.153 |
| A    | @    | 185.199.111.153 |

The previous GoDaddy Website Builder `A record` was removed.

## Domain Verification

GitHub domain ownership was verified using a DNS TXT record:

```text
_github-pages-challenge-alexBlakeGoudemond.absurdlygoud.com
```

The TXT record should remain in place for GitHub's domain verification.

## HTTPS

GitHub Pages are configured with:

```text
Custom domain: absurdlygoud.com
DNS check: successful
Enforce HTTPS: enabled
```

The site is therefore served through:

```text
https://absurdlygoud.com
```