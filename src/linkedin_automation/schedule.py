"""li-schedule: a small publishing queue with a human approval step.

LinkedIn's API has no "publish later" option, so scheduling happens here: you add a post to the queue with a
time, a person approves it, and a runner (cron, every 5 minutes) publishes whatever is both APPROVED and due.
Nothing is ever published unless a person ran `li-schedule approve`.

    li-schedule add post.txt --at "2026-11-03 09:30" [--tz Asia/Kolkata] [--image a.png] [--first-comment "..."]
    li-schedule list
    li-schedule show ID
    li-schedule approve ID          (this is the human "yes")
    li-schedule unapprove ID | cancel ID
    li-schedule run [--dry-run]     (publish approved posts that are due; safe to run from cron)
    li-schedule cron                (print the crontab line to run it every 5 minutes)

Safety: one daily cap (default 2 posts per UTC day), an item is marked "sending" BEFORE it is sent so a crash can
never double-post, and a failed item is never retried automatically.
"""
from __future__ import annotations

import argparse
import json
import os
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import common, lint, post
from .common import load_token, person_urn

DAILY_CAP = int(os.environ.get("LI_SCHEDULE_DAILY_CAP", "2"))
STATUSES = ("draft", "approved", "sending", "sent", "failed", "cancelled")


def queue_dir() -> Path:
    d = common.config_dir() / "queue"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _path(item_id: str) -> Path:
    if not item_id.replace("-", "").isalnum():
        raise SystemExit("Bad id.")
    return queue_dir() / f"{item_id}.json"


def load(item_id: str) -> Dict[str, Any]:
    p = _path(item_id)
    if not p.is_file():
        raise SystemExit(f"No queued post {item_id}.")
    return json.loads(p.read_text())


def save(item: Dict[str, Any]) -> None:
    p = _path(item["id"])
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(item, indent=2, ensure_ascii=False))
    os.replace(tmp, p)


def all_items() -> List[Dict[str, Any]]:
    out = []
    for p in sorted(queue_dir().glob("*.json")):
        try:
            out.append(json.loads(p.read_text()))
        except ValueError:
            continue
    return sorted(out, key=lambda i: i.get("due_utc", ""))


def parse_local(at: str, tz: Optional[str]) -> datetime:
    """'2026-11-03 09:30' in the given IANA zone (default: this computer's zone) -> aware UTC datetime."""
    try:
        naive = datetime.strptime(at.strip(), "%Y-%m-%d %H:%M")
    except ValueError:
        raise SystemExit('Time must look like "2026-11-03 09:30".')
    if tz:
        try:
            from zoneinfo import ZoneInfo
            aware = naive.replace(tzinfo=ZoneInfo(tz))
        except Exception:
            raise SystemExit(f"Unknown time zone: {tz} (use a name like Asia/Kolkata or Europe/London).")
    else:
        aware = naive.astimezone()      # this computer's local zone
        aware = naive.replace(tzinfo=aware.tzinfo)
    return aware.astimezone(timezone.utc)


def sent_today() -> int:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return sum(1 for i in all_items() if i.get("status") in ("sent", "sending") and (i.get("sent_at") or "")[:10] == today)


def add(text: str, due_utc: datetime, images: List[str], first_comment: Optional[str], visibility: str) -> Dict[str, Any]:
    res = lint.check(text)
    if res["errors"]:
        raise SystemExit("The post has errors, so it was not queued:\n" + lint.render(res))
    for im in images:
        if not Path(im).is_file():
            raise SystemExit(f"File not found: {im}")
    item = {
        "id": secrets.token_hex(4), "status": "draft", "text": text, "images": [str(Path(i).resolve()) for i in images],
        "first_comment": first_comment, "visibility": visibility, "due_utc": due_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "lint_score": res["score"],
    }
    save(item)
    return item


def _send(item: Dict[str, Any], tok: Dict[str, Any]) -> str:
    token, author = tok["access_token"], person_urn(tok)
    p = post.base_post(author, item["text"], item.get("visibility", "PUBLIC"))
    if item.get("images"):
        urns = [post.upload_asset(token, author, Path(i), "images") for i in item["images"]]
        p = post.with_images(p, urns)
    urn = post.publish(token, p)
    if item.get("first_comment"):
        post.add_comment(token, author, urn, item["first_comment"])
    return urn


def run(dry: bool = False, now: Optional[datetime] = None) -> List[str]:
    now = now or datetime.now(timezone.utc)
    log: List[str] = []
    due = [i for i in all_items() if i["status"] == "approved" and i["due_utc"] <= now.strftime("%Y-%m-%dT%H:%M:%SZ")]
    if not due:
        return ["Nothing due."]
    tok = None if dry else load_token()
    for item in due:
        if sent_today() >= DAILY_CAP:
            log.append(f"{item['id']}: skipped, the daily cap of {DAILY_CAP} posts is reached (it stays approved for tomorrow).")
            continue
        if dry:
            log.append(f"{item['id']}: WOULD publish now: {item['text'][:60]!r}")
            continue
        item["status"], item["sent_at"] = "sending", now.strftime("%Y-%m-%dT%H:%M:%SZ")
        save(item)                                   # mark first: a crash must never cause a double post
        try:
            urn = _send(item, tok)
            item.update(status="sent", urn=urn, url=post.post_url(urn))
            log.append(f"{item['id']}: published {item['url']}")
        except SystemExit as e:
            item.update(status="failed", error=common.redact(str(e))[:300])
            log.append(f"{item['id']}: FAILED - {item['error']}")
        save(item)
    return log


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="li-schedule", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a_ = sub.add_parser("add"); a_.add_argument("file"); a_.add_argument("--at", required=True); a_.add_argument("--tz")
    a_.add_argument("--image", action="append", default=[]); a_.add_argument("--first-comment"); a_.add_argument("--visibility", default="PUBLIC")
    sub.add_parser("list"); s_ = sub.add_parser("show"); s_.add_argument("id")
    for n in ("approve", "unapprove", "cancel"):
        x = sub.add_parser(n); x.add_argument("id")
    r_ = sub.add_parser("run"); r_.add_argument("--dry-run", action="store_true")
    sub.add_parser("cron")
    a = ap.parse_args(argv)

    if a.cmd == "add":
        item = add(Path(a.file).read_text(), parse_local(a.at, a.tz), a.image, a.first_comment, a.visibility)
        print(f"Queued {item['id']} for {item['due_utc']} (UTC). Status: draft. It will NOT publish until you run: li-schedule approve {item['id']}")
    elif a.cmd == "list":
        for i in all_items():
            print(f"{i['id']}  {i['status']:<9} {i['due_utc']}  {i['text'][:60]!r}")
    elif a.cmd == "show":
        i = load(a.id); print(json.dumps(i, indent=2, ensure_ascii=False))
    elif a.cmd in ("approve", "unapprove", "cancel"):
        i = load(a.id)
        if i["status"] in ("sent", "sending"):
            raise SystemExit("That post was already sent.")
        i["status"] = {"approve": "approved", "unapprove": "draft", "cancel": "cancelled"}[a.cmd]
        if a.cmd == "approve":
            i["approved_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        save(i); print(f"{a.id}: {i['status']}")
    elif a.cmd == "run":
        print("\n".join(run(a.dry_run)))
    elif a.cmd == "cron":
        print(f"*/5 * * * * {sys.executable} -m linkedin_automation.schedule run >> $HOME/.config/linkedin-automation/schedule.log 2>&1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
