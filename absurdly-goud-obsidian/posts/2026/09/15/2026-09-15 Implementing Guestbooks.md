I planned Guestbook work in [[2026-09-14 Investigating Guestbooks]] and had 1 unseen assumption; webmentions.io is all I need. This is not the case - a middleman / worker is still needed. 

Webmention.io's API endpoint does not receive the JSON Payload in an HTTP POST - it accepts 2 URLS (Source and Destination) and then the API fetches the content itself

A request like this should be sent to webmentions.io:

```http
POST https://webmention.io/alexblakegoudemond.com/webmention
source=https://some-url/entry/123
target=https://alexblakegoudemond.com/guestbook/
```

There's no `message` or `name` field in that payload at all. Webmention.io takes those two URLs, then makes its own outbound HTTP request to `source`, and:

1. Confirms the fetched page actually contains a link to `target` (proof you're not making up a mention for a page you don't control)
2. Parses that page's HTML for microformats2 markup (`h-entry`, `p-author`, `p-content`, etc.) to extract the actual message/author/content

It's an API for _registering that a link exists_, not for _submitting data_. The content has to already be sitting at a fetchable URL before you ever call the endpoint, because webmention.io's whole verification model is "I don't trust what you tell me, I'll go look for myself."

That's a deliberate anti-spoofing property of the Webmention spec itself (not a webmention.io quirk) — without the fetch-and-verify step, anyone could POST a fake mention claiming any page said anything about any target, with no proof at all.

## Desired Flow

What I would love is this flow:

```
visitor submits guestbook entry 
→ Worker publishes entry + sends webmention 
→ webmention.io stores it
    ↓
(sits in webmentions.io, invisible to site visitors)
    ↓
I fetch mentions via API whenever I choose
    ↓
I moderate each one
    ↓
approved ones I bring into the site via git commits
→ _data/guestbook.yml → commit
→ makes public content
    ↓
Jekyll rebuilds, now it's live
```

I'm going to pursue Cloudflare Workers because:
- **DDoS prevention**: this isn't a bolt-on feature, it's Cloudflare's core business — Workers run on the same edge network that absorbs some of the largest DDoS attacks on the internet. You get this automatically, no configuration.
- **Rate limiting**: built-in Rate Limiting Rules you can attach directly to your Worker's route — a few clicks, no separate service to wire up. Genuinely useful for a public form endpoint like yours.
- **Ease of use**: no server, no OS, no scaling config, no cold-start tuning. `wrangler deploy` and you're live. KV storage (what the entry pages live in) is likewise zero-ops.
- **Cheap**: free tier is 100,000 requests/day, which is wildly more than a personal guestbook will ever see. You will not pay anything for this use case.

## Answers to Research Questions
I asked questions in [[2026-09-14 Investigating Guestbooks#Research Questions|Investigating Guestbooks Research Questions]], below are the answers:
- cost? 
	- With Cloudflare Workers: Free Tier cost $0 per month, with up to 100_000 daily requests
- setup and maintenance?
	- Setup and maintain in the IDE with [Wrangler](https://developers.cloudflare.com/workers/wrangler/) (in the GitHub Repository) else in the browser
- does it actually work for my guestbook use case?
	- YES! With Webmentions.io
- can I delay retrieval/processing?
	- YES, Webmention.io hold onto the updates for me
- does the service provide persistent storage, or would I need my own database?
	- Webmention.io offers storage
- how long is submitted data retained before I retrieve and 
	- Webmention.io from my research, indefinitely by default
- ingest it into my site?
	- I can do this manually / via a script in time
- how does moderation work?
	- I control it! Bringing content into the site is in my control
- can I export/recover all of my data if I stop using the service?
	- There is a Webmention.io API - so I could. But IndieWeb conventions is about owning my data - so I would prefer to move the posts to my own website as and when I have them

