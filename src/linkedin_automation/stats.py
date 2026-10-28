"""li-stats: read your own post numbers through the official analytics API, spending as few calls as possible.

    li-stats post URN [--metrics IMPRESSION,REACTION,COMMENT,RESHARE]   numbers for one post (one call per metric)
    li-stats me   --metric IMPRESSION [--days 30] [--daily]             one number (or one per day) across ALL your posts
    li-stats followers                                                   your follower count
    li-stats budget                                                      calls used today

Needs the r_member_postAnalytics permission (the "Community Management API" product on the app).
LinkedIn answers ONE post and ONE metric per call and allows 100 calls per member per day on the Development
tier, so this tool keeps a local call counter, caches answers for 6 hours and stops before the limit.
"""
from __future__ import annotations

import argparse
import json
import time
import urllib.parse
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from . import common
from .common import REST, http, load_token, redact, rest_headers

METRICS = ["IMPRESSION", "MEMBERS_REACHED", "REACTION", "COMMENT", "RESHARE", "POST_SAVE", "POST_SEND", "LINK_CLICKS",
           "PREMIUM_CTA_CLICKS", "FOLLOWER_GAINED_FROM_CONTENT", "PROFILE_VIEW_FROM_CONTENT"]   # the last six need version 202604 or later
CACHE_TTL = 6 * 3600


def entity_param(post_urn: str) -> str:
    """entity=(share:urn%3Ali%3Ashare%3A123) or (ugc:urn%3Ali%3AugcPost%3A123). Encoded once: never let a library encode it again."""
    kind = "ugc" if ":ugcPost:" in post_urn else "share"
    return f"({kind}:{urllib.parse.quote(post_urn, safe='')})"


def post_url_query(post_urn: str, metric: str, daily: bool = False, start: Optional[datetime] = None, end: Optional[datetime] = None) -> str:
    q = f"{REST}/memberCreatorPostAnalytics?q=entity&entity={entity_param(post_urn)}&queryType={metric}&aggregation={'DAILY' if daily else 'TOTAL'}"
    if start and end:
        q += "&dateRange=" + date_range(start, end)
    return q


def me_url_query(metric: str, daily: bool = False, start: Optional[datetime] = None, end: Optional[datetime] = None) -> str:
    q = f"{REST}/memberCreatorPostAnalytics?q=me&queryType={metric}&aggregation={'DAILY' if daily else 'TOTAL'}"
    if start and end:
        q += "&dateRange=" + date_range(start, end)
    return q


def date_range(start: datetime, end: datetime) -> str:
    """Rest.li date range: start inclusive, end exclusive."""
    return f"(start:(day:{start.day},month:{start.month},year:{start.year}),end:(day:{end.day},month:{end.month},year:{end.year}))"


def _cache_path():
    return common.config_dir() / "stats-cache.json"


def _cache_get(key: str) -> Optional[Any]:
    try:
        c = json.loads(_cache_path().read_text()).get(key)
        if c and time.time() - c["at"] < CACHE_TTL:
            return c["value"]
    except (OSError, ValueError, KeyError):
        pass
    return None


def _cache_put(key: str, value: Any) -> None:
    try:
        data = json.loads(_cache_path().read_text())
    except (OSError, ValueError):
        data = {}
    data = {k: v for k, v in data.items() if time.time() - v.get("at", 0) < 7 * 86400}
    data[key] = {"at": time.time(), "value": value}
    _cache_path().parent.mkdir(parents=True, exist_ok=True)
    _cache_path().write_text(json.dumps(data))


def fetch(token: str, url: str, cap: int, use_cache: bool = True) -> Dict[str, Any]:
    """One metered call (or a cached answer). Returns {"ok", "count", "elements", "error", "cached"}."""
    if use_cache:
        hit = _cache_get(url)
        if hit is not None:
            return {**hit, "cached": True}
    if common.budget_left(cap) <= 0:
        return {"ok": False, "error": f"Stopped: today's call budget ({cap}) is used up. LinkedIn resets limits at midnight UTC.", "cached": False}
    r = http("GET", url, rest_headers(token, None))
    common.record_call()
    if not r.ok:
        return {"ok": False, "error": common.explain_error(r), "status": r.status, "cached": False}
    els = (r.json() or {}).get("elements") or []
    out = {"ok": True, "count": (els[0].get("count") if els and len(els) == 1 else None), "elements": els, "cached": False}
    if use_cache:
        _cache_put(url, {k: out[k] for k in ("ok", "count", "elements")})
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="li-stats", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cap", type=int, default=common.DEFAULT_BUDGET, help="stop when this many calls were made today (default 90 of LinkedIn's 100)")
    ap.add_argument("--fresh", action="store_true", help="ignore the 6-hour cache")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("post"); p.add_argument("urn"); p.add_argument("--metrics", default="IMPRESSION,REACTION,COMMENT,RESHARE")
    m = sub.add_parser("me"); m.add_argument("--metric", default="IMPRESSION"); m.add_argument("--days", type=int, default=0); m.add_argument("--daily", action="store_true")
    sub.add_parser("followers"); sub.add_parser("budget")
    a = ap.parse_args(argv)

    if a.cmd == "budget":
        print(f"Calls today (UTC): {common.calls_today()} - budget {a.cap} - LinkedIn's member limit {common.MEMBER_DAILY_LIMIT}")
        return 0
    tok = load_token()["access_token"]
    if a.cmd == "followers":
        r = fetch(tok, f"{REST}/memberFollowersCount?q=me", a.cap, not a.fresh)
        print(r["error"] if not r["ok"] else json.dumps(r["elements"], indent=2))
        return 0 if r["ok"] else 1
    if a.cmd == "post":
        metrics = [x.strip().upper() for x in a.metrics.split(",") if x.strip()]
        bad = [x for x in metrics if x not in METRICS]
        if bad:
            raise SystemExit(f"Unknown metric(s): {', '.join(bad)}. Choose from: {', '.join(METRICS)}")
        rows, failed = {}, False
        for mt in metrics:
            r = fetch(tok, post_url_query(a.urn, mt), a.cap, not a.fresh)
            rows[mt] = r["count"] if r["ok"] else r["error"]
            failed |= not r["ok"]
            if not r["ok"] and r.get("status") in (401, 403, 429):
                break
        print(json.dumps({"post": a.urn, **rows}, indent=2))
        return 1 if failed else 0
    end = datetime.now(timezone.utc).date() + timedelta(days=1)
    start = end - timedelta(days=a.days) if a.days else None
    s_dt = datetime(start.year, start.month, start.day) if start else None
    e_dt = datetime(end.year, end.month, end.day) if start else None
    r = fetch(tok, me_url_query(a.metric.upper(), a.daily, s_dt, e_dt), a.cap, not a.fresh)
    print(r["error"] if not r["ok"] else json.dumps(r["elements"] if a.daily else {"metric": a.metric.upper(), "count": r["count"]}, indent=2))
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
