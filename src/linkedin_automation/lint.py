"""li-lint: check a LinkedIn post before it goes out.

Checks length, the opening line, "AI tells", engagement bait, hashtags, links, emoji, formatting and leftovers
like [placeholders]. It never changes your text; it only reports. Exit code 1 means there is a hard error.

    li-lint "your post text"        li-lint --file post.txt        cat post.txt | li-lint -
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Any, Dict, List

MAX_CHARS = 3000   # LinkedIn's limit for the post text

# Phrases and patterns that make a post read as machine-written or as a template. Case-insensitive.
AI_TELLS = [
    "delve", "game-changer", "game changer", "in today's fast-paced world", "in today's digital landscape",
    "unlock the power", "unlock your potential", "leverage", "synergy", "revolutionize", "tapestry", "testament to",
    "navigate the complexities", "ever-evolving", "it's important to note", "it is important to note",
    "let's dive in", "let's dive into", "buckle up", "here's the thing", "i'm thrilled to announce", "i am thrilled to announce",
    "i'm excited to share", "i am excited to share", "excited to announce", "elevate your", "take it to the next level",
    "at the end of the day", "moving the needle", "thought leader", "deep dive", "unpack", "harness the power",
    "in conclusion", "in summary,", "ultimately,", "furthermore,", "moreover,", "seamlessly", "robust solution",
    "cutting-edge", "state-of-the-art", "a game of", "paradigm shift",
]
CLICHES = ["let that sink in", "read that again", "nobody is talking about", "here's what i learned", "hot take:", "unpopular opinion:"]
BAIT = [
    r"comment\s+(yes|below|\"?\w+\"?\s+below)\b", r"like if you agree", r"tag (a|someone|your)", r"follow (me )?for more",
    r"repost\b.*♻", r"\bagree\?\s*$", r"drop a (comment|\U0001F525|emoji)", r"share (this )?if", r"thoughts\?\s*$",
]
PLACEHOLDER = re.compile(r"\[[A-Z][A-Za-z ]{1,30}\]|\{\{.*?\}\}|\bTODO\b|\bXXX+\b|lorem ipsum|<insert|\[insert", re.I)
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿\U0001F000-\U0001F2FF]")
URL = re.compile(r"https?://\S+|\bwww\.\S+", re.I)
HASHTAG = re.compile(r"(?<![\w#])#[A-Za-z][\w]*")
SECRETISH = re.compile(r"\bAQ[A-Za-z0-9_\-]{40,}\b|\b(sk|rk|pk)-[A-Za-z0-9_\-]{20,}|\bghp_[A-Za-z0-9]{20,}|client_secret\s*[=:]\s*\S{8,}", re.I)


def check(text: str, max_hashtags: int = 5, extra_banned: List[str] = None) -> Dict[str, Any]:
    errors: List[str] = []
    warnings: List[str] = []
    notes: List[str] = []
    t = text.replace("\r\n", "\n").strip()
    if not t:
        return {"errors": ["The post is empty."], "warnings": [], "notes": [], "stats": {}, "score": 0}
    lines = t.split("\n")
    first = next((l for l in lines if l.strip()), "")
    words = len(t.split())
    hashtags = HASHTAG.findall(t)
    links = URL.findall(t)
    emoji = EMOJI.findall(t)
    low = t.lower()

    if len(t) > MAX_CHARS:
        errors.append(f"Too long: {len(t)} characters (LinkedIn allows {MAX_CHARS}).")
    if SECRETISH.search(t):
        errors.append("This text contains something that looks like a password, key or token. Remove it.")
    if PLACEHOLDER.search(t):
        errors.append("Unfilled placeholder left in the text (like [Name], {{...}}, TODO or lorem ipsum).")

    hook_words = len(first.split())
    if hook_words > 20 or len(first) > 140:
        warnings.append(f"The opening line is long ({hook_words} words, {len(first)} characters). Readers decide in the first 2-3 lines; "
                        "LinkedIn folds the post with 'see more' after roughly 140-210 characters. Make the first line a single clear promise.")
    if len(t) > 140 and first.strip().endswith(":") and hook_words < 4:
        notes.append("The opening line is only a lead-in. Make sure the line after it still earns the click.")

    hits = sorted({p for p in AI_TELLS + (extra_banned or []) if p.lower() in low})
    if hits:
        warnings.append("Reads like AI or a template: " + ", ".join(f'"{h}"' for h in hits[:8]) + ". Say it the way you would say it to a colleague.")
    cl = sorted({p for p in CLICHES if p in low})
    if cl:
        warnings.append("Overused LinkedIn lines: " + ", ".join(f'"{c}"' for c in cl) + ".")
    for pat in BAIT:
        if re.search(pat, low, re.I | re.M):
            warnings.append("Engagement bait (asking for comments, tags, likes or reposts) tends to feel spammy to readers and rarely brings the people you want.")
            break
    dashes = t.count("—")
    if dashes > 2:
        warnings.append(f"{dashes} em dashes. Heavy dash use is a common AI tell; use full stops or commas.")
    if re.search(r"\bnot (just|only) [^.\n]{3,60}, but (also )?", low):
        warnings.append('The "not just X, but Y" pattern is a strong AI tell. State the point directly.')
    if len(hashtags) > max_hashtags:
        warnings.append(f"{len(hashtags)} hashtags. Keep to {max_hashtags} or fewer, placed at the end.")
    if hashtags and not re.search(r"#\w+\s*$", t.split("\n")[-1]) and any(HASHTAG.search(l) for l in lines[:-1]):
        notes.append("Hashtags are mixed into the text. Putting them in one line at the end reads cleaner.")
    if links:
        warnings.append("A link in the post body. Many writers put the link in the first comment instead (LinkedIn does not document a penalty; it is a widely used habit).")
    if len(emoji) > 3:
        warnings.append(f"{len(emoji)} emoji. Two or three at most keeps it professional.")
    caps = [w for w in re.findall(r"\b[A-Z]{4,}\b", t) if w not in ("AI", "API", "CRM", "SEO", "LLM", "SQL", "DAX")]
    if len(caps) > 3:
        warnings.append("Several ALL-CAPS words read as shouting.")
    long_par = [p for p in re.split(r"\n\s*\n", t) if len(p) > 450 or p.count("\n") > 5]
    if long_par:
        warnings.append("A very long paragraph. Break it up: short paragraphs (1-3 lines) are easier to read on a phone.")
    one_liners = sum(1 for p in re.split(r"\n\s*\n", t) if "\n" not in p.strip())
    paragraphs = max(1, len(re.split(r"\n\s*\n", t)))
    if paragraphs >= 10 and one_liners / paragraphs > 0.8:
        notes.append("Almost every paragraph is a single line. A few longer paragraphs would add rhythm.")
    if words < 40:
        notes.append(f"Short post ({words} words). Fine for a sharp thought; add a concrete detail if it feels thin.")
    if words > 400:
        notes.append(f"Long post ({words} words). Check that every paragraph earns its place.")

    score = max(0, 100 - 25 * len(errors) - 6 * len(warnings) - 1 * len(notes))
    return {
        "errors": errors, "warnings": warnings, "notes": notes, "score": score,
        "stats": {"characters": len(t), "words": words, "lines": len(lines), "opening_line_words": hook_words,
                  "hashtags": len(hashtags), "links": len(links), "emoji": len(emoji)},
    }


def render(res: Dict[str, Any]) -> str:
    out = []
    s = res.get("stats") or {}
    if s:
        out.append(f"Post check: {s['characters']} characters, {s['words']} words, opening line {s['opening_line_words']} words, "
                   f"{s['hashtags']} hashtags, {s['links']} links. Score {res['score']}/100")
    for label, key in (("ERROR", "errors"), ("WARNING", "warnings"), ("NOTE", "notes")):
        for m in res[key]:
            out.append(f"  {label}: {m}")
    if not (res["errors"] or res["warnings"] or res["notes"]):
        out.append("  Clean. Nothing to fix.")
    return "\n".join(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="li-lint", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("text", nargs="?", help="the post text, or - to read standard input")
    ap.add_argument("--file")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--max-hashtags", type=int, default=5)
    ap.add_argument("--banned", help="a file with extra phrases to flag, one per line")
    a = ap.parse_args(argv)
    if a.file:
        text = open(a.file, encoding="utf8").read()
    elif a.text == "-" or (a.text is None and not sys.stdin.isatty()):
        text = sys.stdin.read()
    elif a.text:
        text = a.text
    else:
        ap.error("give the text, --file, or pipe it in")
    extra = [l.strip() for l in open(a.banned, encoding="utf8")] if a.banned else None
    res = check(text, a.max_hashtags, extra)
    print(json.dumps(res, indent=2) if a.json else render(res))
    return 1 if res["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
