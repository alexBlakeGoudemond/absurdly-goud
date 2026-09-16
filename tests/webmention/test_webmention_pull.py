#!/usr/bin/env python3
"""
test_webmention_api.py

Smoke test: proves your token works and you can talk to the
webmention.io API before wiring up the full pull script.

USAGE
-----
    # Token resolution order (first one found wins):
    #   1. --token flag
    #   2. WEBMENTION_IO_TOKEN in a local .env file (see .env.example)
    #   3. WEBMENTION_IO_TOKEN environment variable

    python test_webmention_api.py
    python test_webmention_api.py --token xxxxxxxx
"""

import argparse
import json
import os
import sys

import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def main():
    ap = argparse.ArgumentParser(description="Smoke test for the webmention.io API.")
    ap.add_argument("--token", default=os.environ.get("WEBMENTION_IO_TOKEN"),
                    help="API token (or set WEBMENTION_IO_TOKEN via .env / env var)")
    args = ap.parse_args()

    token = args.token
    if not token:
        sys.exit(
            "No token found. Either:\n"
            "  --token xxxxxxxx\n"
            "  or put WEBMENTION_IO_TOKEN=xxxxxxxx in a .env file\n"
            "  or export WEBMENTION_IO_TOKEN=xxxxxxxx"
        )

    resp = requests.get(
        "https://webmention.io/api/mentions.jf2",
        params={"token": token, "per-page": 1},
        timeout=15,
    )
    print("HTTP status:", resp.status_code)
    resp.raise_for_status()

    data = resp.json()
    children = data.get("children", [])
    print(f"Connected OK. Feed type: {data.get('type')!r}, entries returned: {len(children)}")

    if children:
        print("\nMost recent mention (raw JF2):")
        print(json.dumps(children[0], indent=2)[:1000])
    else:
        print("\nNo mentions on the account yet, but the token + request worked.")


if __name__ == "__main__":
    main()