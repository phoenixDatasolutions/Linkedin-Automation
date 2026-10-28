"""li-secrets-scan: stop keys, tokens and passwords from reaching GitHub.

    li-secrets-scan                     scan every file git tracks or would add
    li-secrets-scan --staged            scan only what is staged for the next commit (used by the pre-commit hook)
    li-secrets-scan --history           scan every line ever committed (run before the first push)
    li-secrets-scan --install-hook      install a git pre-commit hook that runs --staged and blocks the commit
    li-secrets-scan PATH [PATH...]      scan specific files

A line that contains the text  secretscan:allow  is skipped (use it only for obvious fakes in tests).

Extra private strings to block (your client ID, internal host names, a person's name...) can be listed one per line
in <config folder>/secretscan-extra.txt, OUTSIDE the repository, or in the LI_SECRETSCAN_EXTRA environment variable
(comma separated). Matches are reported without printing the secret itself. Exit code 1 = something was found.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List, Tuple

from . import common

PATTERNS: List[Tuple[str, re.Pattern]] = [
    ("LinkedIn access/refresh token", re.compile(r"\bAQ[A-Za-z0-9_\-]{60,}")),
    ("Private key block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("GitHub token", re.compile(r"\b(ghp|gho|ghu|ghs|ghr|github_pat)_[A-Za-z0-9_]{20,}")),
    ("OpenAI/Anthropic style key", re.compile(r"\b(sk|rk)-(ant-|proj-)?[A-Za-z0-9_\-]{20,}")),
    ("AWS access key id", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("Telegram bot token", re.compile(r"\b\d{8,10}:AA[A-Za-z0-9_\-]{33}\b")),
    ("Slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9\-]{10,}")),
    ("Database URL with password", re.compile(r"\b(postgres(ql)?|mysql|mongodb(\+srv)?)://[^:\s/@]+:[^@\s]{3,}@")),
    ("Secret assigned a real-looking value",
     re.compile(r"(?i)\b[A-Z0-9_]*(client_secret|secret|password|passwd|api_?key|access_?token|refresh_?token|private_?key)[A-Z0-9_]*\s*[=:]\s*['\"]?([A-Za-z0-9_\-/+=.]{12,})")),
]
PLACEHOLDER = re.compile(r"(?i)(your[_\- ]|<|\$\{|\{\{|x{4,}|\*\*\*|example|placeholder|changeme|dummy|hidden|redacted|os\.environ|getenv|process\.env|\.\.\.)")
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", ".egg-info"}
SKIP_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf", ".zip", ".gz", ".woff", ".woff2", ".ttf", ".mp4"}
MAX_BYTES = 2_000_000


def extra_terms() -> List[str]:
    terms = [t.strip() for t in os.environ.get("LI_SECRETSCAN_EXTRA", "").split(",") if t.strip()]
    p = common.config_dir() / "secretscan-extra.txt"
    if p.is_file():
        terms += [l.strip() for l in p.read_text().splitlines() if l.strip() and not l.startswith("#")]
    return [t for t in terms if len(t) >= 4]


def scan_text(text: str, name: str, extras: Iterable[str] = ()) -> List[str]:
    """Return findings as 'file:line: kind' (the matched text is never included)."""
    out = []
    for n, line in enumerate(text.splitlines(), 1):
        if "secretscan:allow" in line:      # an intentional fake (for example in a test); the marker must be on the same line
            continue
        for kind, pat in PATTERNS:
            m = pat.search(line)
            if not m:
                continue
            if kind.startswith("Secret assigned"):
                val = m.group(m.lastindex or 0)
                if PLACEHOLDER.search(line) or PLACEHOLDER.search(val) or not re.search(r"\d", val) and not re.search(r"[A-Z]", val):
                    continue
            elif PLACEHOLDER.search(m.group(0)):
                continue
            out.append(f"{name}:{n}: {kind}")
        for t in extras:
            if t.lower() in line.lower():
                out.append(f"{name}:{n}: a private term from your block list")
    return out


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=False).stdout


def files_to_scan(staged: bool) -> List[str]:
    names = _git("diff", "--cached", "--name-only", "--diff-filter=ACM").split("\n") if staged else \
        (_git("ls-files").split("\n") + _git("ls-files", "--others", "--exclude-standard").split("\n"))
    return [n for n in names if n.strip()]


def scan_file(path: str, extras: Iterable[str]) -> List[str]:
    p = Path(path)
    if not p.is_file() or p.suffix.lower() in SKIP_EXT or any(part in SKIP_DIRS for part in p.parts):
        return []
    try:
        if p.stat().st_size > MAX_BYTES:
            return []
        return scan_text(p.read_text(errors="ignore"), path, extras)
    except OSError:
        return []


def scan_history(extras: Iterable[str]) -> List[str]:
    log = _git("log", "--all", "-p", "--no-color", "--unified=0")
    findings, commit = [], ""
    for line in log.splitlines():
        if line.startswith("commit "):
            commit = line.split()[1][:8]
        elif line.startswith("+") and not line.startswith("+++"):
            findings += [f"history {commit}: {f.split(': ', 1)[1]}" for f in scan_text(line[1:], "line", extras)]
    return findings


HOOK = """#!/bin/sh
# installed by li-secrets-scan: blocks a commit that contains keys, tokens or passwords
li-secrets-scan --staged || { echo "Commit blocked: remove the secret(s) above."; exit 1; }
"""


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="li-secrets-scan", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--staged", action="store_true")
    ap.add_argument("--history", action="store_true")
    ap.add_argument("--install-hook", action="store_true")
    a = ap.parse_args(argv)
    if a.install_hook:
        d = Path(_git("rev-parse", "--git-dir").strip() or ".git") / "hooks"
        d.mkdir(parents=True, exist_ok=True)
        h = d / "pre-commit"
        h.write_text(HOOK)
        h.chmod(0o755)
        print(f"Installed {h}")
        return 0
    extras = extra_terms()
    findings: List[str] = []
    if a.history:
        findings = scan_history(extras)
    else:
        for f in (a.paths or files_to_scan(a.staged)):
            findings += scan_file(f, extras)
    if findings:
        print("POSSIBLE SECRETS FOUND (values are not shown):")
        for f in findings[:50]:
            print("  " + f)
        return 1
    print("No secrets found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
