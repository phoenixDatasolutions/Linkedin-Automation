"""li-post: write a post to LinkedIn through the official Posts API - with a safety catch.

By default NOTHING is sent: the command checks the text, shows exactly what would be published and stops.
Publishing needs --publish and a typed confirmation (or --yes after a human has approved the draft).

    li-post text   "Your post"            [--file post.txt] [--first-comment "..."]
    li-post image  "Caption" a.png [b.png ...]
    li-post document "Caption" deck.pdf --title "Deck title"
    li-post poll   "Question?" -o "A" -o "B" [-o "C"] --days 3
    li-post article "Caption" https://example.com --title "T" --description "D" [--thumbnail pic.png]
    li-post delete urn:li:share:123 --publish        (removes one of your own posts)
"""
from __future__ import annotations

import argparse
import json
import mimetypes
import sys
import urllib.parse
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import common, lint, littletext
from .common import REST, http, load_token, person_urn, redact, rest_headers

MAX_IMAGE_BYTES = 36_000_000 // 3   # LinkedIn's limit is by pixels (about 36 million); this is only a sanity check on file size
MAX_DOC_BYTES = 100 * 1024 * 1024
POLL_DAYS = {1: "ONE_DAY", 3: "THREE_DAYS", 7: "SEVEN_DAYS", 14: "FOURTEEN_DAYS"}


# ---------------------------------------------------------------- payload builders (pure functions, easy to test)
def base_post(author: str, text: str, visibility: str = "PUBLIC") -> Dict[str, Any]:
    if visibility not in ("PUBLIC", "CONNECTIONS", "LOGGED_IN"):
        raise SystemExit("visibility must be PUBLIC, CONNECTIONS or LOGGED_IN")
    return {
        "author": author,
        "commentary": littletext.to_commentary(text),
        "visibility": visibility,
        "distribution": {"feedDistribution": "MAIN_FEED", "targetEntities": [], "thirdPartyDistributionChannels": []},
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }


def with_images(post: Dict[str, Any], image_urns: List[str], alt: Optional[str] = None) -> Dict[str, Any]:
    if len(image_urns) == 1:
        media: Dict[str, Any] = {"id": image_urns[0]}
        if alt:
            media["altText"] = alt
        post["content"] = {"media": media}
    elif 2 <= len(image_urns) <= 20:
        post["content"] = {"multiImage": {"images": [{"id": u, **({"altText": alt} if alt else {})} for u in image_urns]}}
    else:
        raise SystemExit("Use 1 image, or between 2 and 20 images.")
    return post


def with_document(post: Dict[str, Any], doc_urn: str, title: str) -> Dict[str, Any]:
    post["content"] = {"media": {"title": title, "id": doc_urn}}
    return post


def with_poll(post: Dict[str, Any], question: str, options: List[str], days: int) -> Dict[str, Any]:
    if len(question) > 140:
        raise SystemExit("A poll question can be at most 140 characters.")
    if not 2 <= len(options) <= 4 or any(len(o) > 30 for o in options):
        raise SystemExit("A poll needs 2 to 4 options of at most 30 characters each.")
    if days not in POLL_DAYS:
        raise SystemExit("Poll days must be 1, 3, 7 or 14.")
    post["content"] = {"poll": {
        "question": question, "options": [{"text": o} for o in options],
        "settings": {"duration": POLL_DAYS[days], "voteSelectionType": "SINGLE_VOTE", "isVoterVisibleToAuthor": True},
    }}
    return post


def with_article(post: Dict[str, Any], url: str, title: str, description: str, thumbnail_urn: Optional[str]) -> Dict[str, Any]:
    art: Dict[str, Any] = {"source": url, "title": title, "description": description}   # the API does not scrape links: all three are required in practice
    if thumbnail_urn:
        art["thumbnail"] = thumbnail_urn
    post["content"] = {"article": art}
    return post


def comment_body(actor: str, post_urn: str, text: str) -> Dict[str, Any]:
    return {"actor": actor, "object": post_urn, "message": {"text": littletext.to_commentary(text)}}


# ---------------------------------------------------------------- calls
def _call(method: str, url: str, token: str, body: Optional[bytes] = None, content_type: Optional[str] = "application/json",
          extra: Optional[Dict[str, str]] = None) -> common.Reply:
    h = rest_headers(token, content_type)
    h.update(extra or {})
    r = http(method, url, h, body)
    common.record_call()
    return r


def upload_asset(token: str, owner: str, path: Path, kind: str) -> str:
    """Upload an image ("images") or document ("documents"). Returns the URN to use in a post."""
    data = path.read_bytes()
    limit = MAX_DOC_BYTES if kind == "documents" else MAX_IMAGE_BYTES
    if len(data) > limit:
        raise SystemExit(f"{path.name} is too large.")
    init = _call("POST", f"{REST}/{kind}?action=initializeUpload", token, json.dumps({"initializeUploadRequest": {"owner": owner}}).encode())
    if not init.ok:
        raise SystemExit(f"Could not start the {kind[:-1]} upload. {common.explain_error(init)}")
    v = (init.json() or {}).get("value", {})
    upload_url, urn = v.get("uploadUrl"), v.get("image") or v.get("document")
    if not upload_url or not urn:
        raise SystemExit("LinkedIn did not return an upload address.")
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    put = http("PUT", upload_url, {"Authorization": f"Bearer {token}", "Content-Type": mime}, data, timeout=120)
    common.record_call()
    if not put.ok:
        raise SystemExit(f"Upload of {path.name} failed. {common.explain_error(put)}")
    return urn


def publish(token: str, payload: Dict[str, Any]) -> str:
    r = _call("POST", f"{REST}/posts", token, json.dumps(payload).encode())
    if r.status != 201:
        raise SystemExit(f"LinkedIn did not publish the post. {common.explain_error(r)}\n{redact((r.body or b'').decode('utf8', 'replace')[:300])}")
    return r.header("x-restli-id")


def add_comment(token: str, actor: str, post_urn: str, text: str) -> bool:
    enc = urllib.parse.quote(post_urn, safe="")
    r = _call("POST", f"{REST}/socialActions/{enc}/comments", token, json.dumps(comment_body(actor, post_urn, text)).encode())
    return r.status == 201


def delete_post(token: str, urn: str) -> bool:
    r = _call("DELETE", f"{REST}/posts/{urllib.parse.quote(urn, safe='')}", token, None, None)
    return r.status == 204


def post_url(urn: str) -> str:
    return f"https://www.linkedin.com/feed/update/{urn}/"


# ---------------------------------------------------------------- command line
def _text_arg(a) -> str:
    t = Path(a.file).read_text() if getattr(a, "file", None) else a.text
    if not t or not t.strip():
        raise SystemExit("The post text is empty.")
    return t


def _confirm(a) -> bool:
    """True when it is OK to publish. A dry run prints a notice and returns False."""
    if not a.publish:
        print("\nDRY RUN: nothing was sent. Add --publish to send it for real.")
        return False
    if a.yes:
        return True
    if not sys.stdin.isatty():
        raise SystemExit("Refusing to publish without a person confirming. Re-run in a terminal, or pass --yes after the draft was approved.")
    if input(f"\nType the word publish to post this to LinkedIn now: ").strip().lower() != "publish":
        raise SystemExit("Cancelled. Nothing was posted.")
    return True


def _author(a, token) -> str:
    if a.org:
        return f"urn:li:organization:{a.org}"
    return person_urn(token)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="li-post", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    opts = argparse.ArgumentParser(add_help=False)
    opts.add_argument("--visibility", default="PUBLIC", choices=["PUBLIC", "CONNECTIONS", "LOGGED_IN"])
    opts.add_argument("--org", help="post as a Company Page (organization id). Needs w_organization_social and a Page role")
    opts.add_argument("--publish", action="store_true", help="actually send it (default is a dry run)")
    opts.add_argument("--yes", action="store_true", help="skip the typed confirmation (only after a person approved the draft)")
    opts.add_argument("--first-comment", help="add this as the first comment right after posting")
    opts.add_argument("--no-lint", action="store_true", help="skip the writing check")
    sub = ap.add_subparsers(dest="kind", required=True)
    t = sub.add_parser("text", parents=[opts]); t.add_argument("text", nargs="?"); t.add_argument("--file")
    i = sub.add_parser("image", parents=[opts]); i.add_argument("text"); i.add_argument("images", nargs="+"); i.add_argument("--alt")
    d = sub.add_parser("document", parents=[opts]); d.add_argument("text"); d.add_argument("path"); d.add_argument("--title", required=True)
    po = sub.add_parser("poll", parents=[opts]); po.add_argument("question"); po.add_argument("-o", "--option", action="append", required=True)
    po.add_argument("--days", type=int, default=3); po.add_argument("--text", default="")
    ar = sub.add_parser("article", parents=[opts]); ar.add_argument("text"); ar.add_argument("url"); ar.add_argument("--title", required=True)
    ar.add_argument("--description", required=True); ar.add_argument("--thumbnail")
    de = sub.add_parser("delete", help="delete one of your posts", parents=[opts]); de.add_argument("urn")
    a = ap.parse_args(argv)

    if a.kind == "delete":
        if not a.publish:
            print(f"DRY RUN: would delete {a.urn}. Add --publish to delete it for real.")
            return 0
        tok = load_token()
        if not a.yes and (not sys.stdin.isatty() or input("Type the word delete to remove this post: ").strip().lower() != "delete"):
            raise SystemExit("Cancelled. Nothing was deleted.")
        print("Deleted." if delete_post(tok["access_token"], a.urn) else "LinkedIn did not delete it (it may already be gone).")
        return 0

    text = a.question if a.kind == "poll" and not a.text else (a.text if a.kind == "poll" else _text_arg(a))
    if not a.no_lint and a.kind != "poll":
        res = lint.check(text)
        print(lint.render(res))
        if res["errors"]:
            raise SystemExit("Fix the errors above first (or use --no-lint if you are sure).")

    tok = load_token(required=a.publish)            # a dry run works without being signed in
    token = tok["access_token"] if tok else "DRY-RUN"
    author = _author(a, tok) if tok else "urn:li:person:DRY-RUN"

    placeholder = lambda n: [f"urn:li:image:PLACEHOLDER{k}" for k in range(n)]
    post = base_post(author, text, a.visibility)
    if a.kind == "image":
        paths = [Path(p) for p in a.images]
        missing = [str(p) for p in paths if not p.is_file()]
        if missing:
            raise SystemExit(f"File not found: {', '.join(missing)}")
        post = with_images(post, placeholder(len(paths)), a.alt)
    elif a.kind == "document":
        if not Path(a.path).is_file():
            raise SystemExit(f"File not found: {a.path}")
        post = with_document(post, "urn:li:document:PLACEHOLDER", a.title)
    elif a.kind == "poll":
        post = with_poll(post, a.question, a.option, a.days)
    elif a.kind == "article":
        post = with_article(post, a.url, a.title, a.description, "urn:li:image:PLACEHOLDER" if a.thumbnail else None)

    print("\n--- This is what would be sent (assets are uploaded first when you publish) ---")
    print(json.dumps(post, indent=2, ensure_ascii=False))
    if a.first_comment:
        print(f"\nFirst comment: {a.first_comment}")
    if not _confirm(a):
        return 0

    # real run: upload assets, swap the placeholders, publish
    if a.kind == "image":
        urns = [upload_asset(token, author, Path(p), "images") for p in a.images]
        post = with_images(base_post(author, text, a.visibility), urns, a.alt)
    elif a.kind == "document":
        post = with_document(base_post(author, text, a.visibility), upload_asset(token, author, Path(a.path), "documents"), a.title)
    elif a.kind == "article" and a.thumbnail:
        post = with_article(base_post(author, text, a.visibility), a.url, a.title, a.description, upload_asset(token, author, Path(a.thumbnail), "images"))
    urn = publish(token, post)
    print(f"\nPublished: {post_url(urn)}")
    if a.first_comment:
        print("First comment added." if add_comment(token, author, urn, a.first_comment) else "The post is live, but the first comment could not be added. Add it by hand.")
    print(f"(calls made today: {common.calls_today()} of {common.MEMBER_DAILY_LIMIT})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
