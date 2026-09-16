#!/usr/bin/env python3
"""
pull_webmentions.py

Pull webmentions from the webmention.io API within a time window and
convert them into YAML records suitable for an Obsidian
`data/guestbook.yml` file that you moderate by hand.

The webmention.io API only supports a server-side `since` filter (no
native `until`), so this script fetches everything from --from onward
and then applies the --to boundary locally.

USAGE
-----
    # Token resolution order (first one found wins):
    #   1. --token flag
    #   2. WEBMENTION_IO_TOKEN in a local .env file (see .env.example)
    #   3. WEBMENTION_IO_TOKEN environment variable

    # Everything since Sep 1st, printed to stdout
    python pull_webmentions.py --from 2026-09-01

    # A specific window
    python pull_webmentions.py --from 2026-09-01 --to 2026-09-15T12:00:00Z

    # Merge new entries straight into your vault's guestbook file
    python pull_webmentions.py --from 2026-09-01 --out data/guestbook.yml

    # Pass the token explicitly instead of using .env / the environment
    python pull_webmentions.py --from 2026-09-01 --token xxxxxxxx

PARAMETERS (all easy to change — see the argparse block below)
----------------------------------------------------------------
    --from      Start of window. ISO-8601 or plain YYYY-MM-DD. REQUIRED.
    --to        End of window. ISO-8601. Defaults to now().
    --domain    webmention.io domain filter (optional).
    --token     API token. See resolution order above.
    --per-page  API page size (default 100).
    --out       Path to merge/write YAML into. Prints to stdout if omitted.
    --status    Moderation status stamped on newly pulled entries
                (default: pending). Existing entries in --out are left
                untouched, so re-running never resets your moderation.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

import requests
import yaml

try:
    from dotenv import load_dotenv
    load_dotenv()  # quietly no-ops if there's no .env file present
except ImportError:
    pass  # python-dotenv not installed — .env just won't be read; env vars/--token still work

API_URL = "https://webmention.io/api/mentions.jf2"


def parse_date(date):
    """Accepts 'YYYY-MM-DD', or full ISO-8601 (with or without a 'Z')."""
    if date is None:
        return None
    date = date.strip()
    if len(date) == 10:  # bare date
        date += "T00:00:00+00:00"
    date = date.replace("Z", "+00:00")
    dt = datetime.fromisoformat(date)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def fetch_all(token, since_iso, domain=None, per_page=100):
    """Page through the API starting at since_iso until a short page ends it."""
    entries = []
    page = 0
    while True:
        params = {
            "token": token,
            "since": since_iso,
            "per-page": per_page,
            "page": page,
        }
        if domain:
            params["domain"] = domain

        resp = requests.get(API_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        children = data.get("children", [])
        if not children:
            break

        entries.extend(children)
        if len(children) < per_page:
            break
        page += 1

    return entries


def in_window(entry, start, end):
    raw = entry.get("wm-received") or entry.get("published")
    if not raw:
        return True  # keep undated entries rather than silently dropping them
    try:
        dt = parse_date(raw)
    except ValueError:
        return True
    if start and dt < start:
        return False
    if end and dt > end:
        return False
    return True


def to_guestbook_record(entry, default_status):
    author = entry.get("author") or {}
    content = entry.get("content") or {}
    return {
        "id": str(entry.get("wm-id")),
        "status": default_status,  # pending | approved | rejected
        "type": entry.get("wm-property", "mention-of"),
        "author": {
            "name": author.get("name"),
            "url": author.get("url"),
            "photo": author.get("photo"),
        },
        "target": entry.get("wm-target") or entry.get("target"),
        "source": entry.get("url") or entry.get("wm-source"),
        "content": content.get("text", ""),
        "published": entry.get("published"),
        "received": entry.get("wm-received"),
    }


def load_existing(path):
    if path and os.path.exists(path):
        with open(path) as f:
            data = yaml.safe_load(f) or []
            if isinstance(data, list):
                return data
    return []


def main():
    ap = argparse.ArgumentParser(
        description="Pull webmention.io mentions into guestbook YAML records."
    )
    ap.add_argument("--from", dest="from_time", required=True,
                    help="Start of window: ISO-8601 or YYYY-MM-DD")
    ap.add_argument("--to", dest="to_time", default=None,
                    help="End of window: ISO-8601 (default: now)")
    ap.add_argument("--domain", default=None, help="webmention.io domain filter")
    ap.add_argument("--token", default=os.environ.get("WEBMENTION_IO_TOKEN"),
                    help="API token (or set WEBMENTION_IO_TOKEN)")
    ap.add_argument("--per-page", type=int, default=100)
    ap.add_argument("--out", default=None,
                    help="Path to merge/write YAML (e.g. data/guestbook.yml). "
                         "Prints to stdout if omitted.")
    ap.add_argument("--status", default="pending",
                    help="Status stamped on newly pulled entries")
    args = ap.parse_args()

    if not args.token:
        sys.exit("No API token provided. Pass --token or set WEBMENTION_IO_TOKEN.")

    start = parse_date(args.from_time)
    end = parse_date(args.to_time) if args.to_time else datetime.now(timezone.utc)

    if end < start:
        sys.exit("--to is earlier than --from — check your window.")

    since_iso = start.isoformat()
    raw_entries = fetch_all(args.token, since_iso, domain=args.domain, per_page=args.per_page)
    windowed = [e for e in raw_entries if in_window(e, start, end)]

    existing = load_existing(args.out)
    existing_ids = {str(r.get("id")) for r in existing}

    new_records = [to_guestbook_record(e, args.status) for e in windowed]
    new_records = [r for r in new_records if r["id"] not in existing_ids]

    print(
        f"Fetched {len(raw_entries)} total since {since_iso}, "
        f"{len(windowed)} fell in window, {len(new_records)} are new.",
        file=sys.stderr,
    )

    combined = existing + new_records
    yaml_text = yaml.safe_dump(combined, sort_keys=False, allow_unicode=True, width=100)

    if args.out:
        out_dir = os.path.dirname(args.out)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        with open(args.out, "w") as f:
            f.write(yaml_text)
        print(f"Wrote {len(combined)} total records to {args.out}", file=sys.stderr)
    else:
        print(yaml_text)


if __name__ == "__main__":
    main()