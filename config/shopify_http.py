#!/usr/bin/env python3
"""One retry policy for every Shopify call the scheduled job makes.

Scheduled run #159 (2026-09-13 16:29 UTC) failed on a single
`HTTP 500 {"errors":"Internal Server Error"}` from Shopify inside
fix_locations.py. The next three runs passed untouched, so nothing was wrong
with the store; the job simply had no tolerance for a one-off 5xx. Reading the
other five steps found the same gap everywhere: sync_inventory and margin_guard
did not retry at all, not even a 429, and guard_unshippable, kit_margins and
verify_kit_inventory retried 429 at most. Six copies of the same helper had
drifted into six different policies.

Retried: 429 (rate limit), 500/502/503/504 (Shopify's transient errors), and
transport failures (dropped connection, timeout). Anything else (401, 404, 422)
is a real answer and is raised at once.

ONLY FOR IDEMPOTENT CALLS. Every caller today is a read, a GraphQL query, or an
`inventory_levels/set`, which writes an absolute figure and so is safe to
repeat. Do not route a create (a product, an order, a fulfilment) through here
without thinking about what a retry after a landed-but-unacknowledged request
would do.
"""
import http.client
import json
import time
import urllib.error
import urllib.request

RETRY_STATUS = (429, 500, 502, 503, 504)
TRANSIENT = (urllib.error.URLError, ConnectionError, TimeoutError,
             http.client.HTTPException)


def urlopen_json(req, timeout=120, tries=6, pause=0.0):
    """Open `req` and parse the JSON body, retrying transient failures.

    `pause` is slept after every success, for callers that pace themselves under
    Shopify's 2 calls/second REST cap. HTTPError is a subclass of URLError, so
    it is handled first and a 4xx is never mistaken for a transport hiccup.
    """
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                body = r.read().decode()
            if pause:
                time.sleep(pause)
            return json.loads(body) if body.strip() else {}
        except urllib.error.HTTPError as exc:
            if exc.code in RETRY_STATUS and attempt < tries - 1:
                time.sleep(min(2 ** attempt, 30))
                continue
            raise
        except TRANSIENT:
            if attempt < tries - 1:
                time.sleep(min(2 ** attempt, 30))
                continue
            raise
    return {}
