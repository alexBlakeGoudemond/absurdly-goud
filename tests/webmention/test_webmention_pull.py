import os
import unittest
from pathlib import Path

import requests

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

from scripts.webmention.webmention_pull import API_URL

# Anchored to this file's location (tests/webmention/ -> repo root is two
# levels up) rather than a bare relative path, so this resolves correctly
# no matter what directory you invoke pytest/unittest from.
_THIS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _THIS_DIR.parent.parent
DEFAULT_ENV_FILE = _REPO_ROOT / '.env' / 'webmentions.io.env'


def _resolve_token():
    """Loads WEBMENTION_IO_TOKEN the same way webmention_pull.py does
    (dotenv file, utf-8-sig safe for a BOM'd file, falls back to a real
    env var), so this test never drifts out of sync with the real script."""
    env_file = os.environ.get('WEBMENTION_ENV_FILE', str(DEFAULT_ENV_FILE))
    if load_dotenv is not None and os.path.exists(env_file):
        load_dotenv(env_file, encoding='utf-8-sig')

    token = os.environ.get('WEBMENTION_IO_TOKEN')
    return token.strip().strip('"').strip("'") if token else None


class TestWebmentionIOAPIConnectivity(unittest.TestCase):
    """Live sanity check against the real webmention.io API -- not a unit
    test. Requires a real WEBMENTION_IO_TOKEN (.env/webmentions.io.env or
    the environment); skips itself automatically when none is configured,
    so it never fails CI or a machine without credentials set up.

    Run on its own for a quick manual check:
        python -m unittest tests.webmention.test_webmention_api -v
    """

    @classmethod
    def setUpClass(cls):
        cls.token = _resolve_token()
        if not cls.token:
            raise unittest.SkipTest(
                'No WEBMENTION_IO_TOKEN configured (.env/webmentions.io.env '
                'or environment) -- skipping live API sanity check.'
            )

    def test_api_responds_with_200(self):
        response = requests.get(
            API_URL, params={'token': self.token, 'per-page': 1}, timeout=15
        )

        self.assertEqual(response.status_code, 200)

    def test_response_is_a_valid_jf2_feed(self):
        response = requests.get(
            API_URL, params={'token': self.token, 'per-page': 1}, timeout=15
        )
        data = response.json()

        self.assertIn('type', data)
        self.assertIn('children', data)
        self.assertIsInstance(data['children'], list)

    def test_bad_token_is_rejected(self):
        # Confirms failures look like failures rather than silently
        # returning an empty-but-200 feed -- catches the exact bug we hit
        # when the token was accidentally the full feed URL, not the token.
        response = requests.get(
            API_URL,
            params={'token': 'definitely-not-a-real-token', 'per-page': 1},
            timeout=15,
        )

        self.assertNotEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main()