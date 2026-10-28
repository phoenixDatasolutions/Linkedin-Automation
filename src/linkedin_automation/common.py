"""Shared plumbing: where credentials live, HTTP calls, the daily call ledger and secret redaction.

Rules this module enforces for every command:
  * Secrets are read from environment variables or a private config folder, never from the repo.
  * The token file is written with owner-only permissions (0600) and is never printed.
  * Anything that is printed or logged goes through redact().
"""
from __future__ import annotations

import json
import os
import re
import stat
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

API_BASE = "https://api.linkedin.com"
REST = f"{API_BASE}/rest"
OAUTH_BASE = "https://www.linkedin.com/oauth/v2"
DEFAULT_VERSION = "202610"          # LinkedIn API version header (YYYYMM). Override with LINKEDIN_API_VERSION.
MEMBER_DAILY_LIMIT = 100            # Community Management Development tier: calls per member per day
DEFAULT_BUDGET = 90                 # stop here to keep a safety margin


def config_dir() -> Path:
    base = os.environ.get("LINKEDIN_AUTOMATION_HOME")
    if base:
        return Path(base).expanduser()
    xdg = os.environ.get("XDG_CONFIG_HOME")
    return (Path(xdg) if xdg else Path.home() / ".config") / "linkedin-automation"


def api_version() -> str:
    return os.environ.get("LINKEDIN_API_VERSION", DEFAULT_VERSION)


# ---------------------------------------------------------------- secrets and redaction
_SECRET_NAMES = ("LINKEDIN_CLIENT_SECRET", "LINKEDIN_ACCESS_TOKEN", "LINKEDIN_REFRESH_TOKEN")
_TOKENISH = re.compile(r"\bAQ[A-Za-z0-9_\-]{40,}\b")
_BEARER = re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._\-]{20,}")
_KV = re.compile(r"(?i)((?:client_secret|access_token|refresh_token|code)=)[^&\s\"']+")


def redact(text: Any) -> str:
    """Remove anything that looks like a LinkedIn token or a configured secret from text."""
    s = str(text)
    for name in _SECRET_NAMES:
        v = os.environ.get(name)
        if v and len(v) >= 8:
            s = s.replace(v, "<hidden>")
    s = _BEARER.sub(r"\1<hidden>", s)
    s = _KV.sub(r"\1<hidden>", s)
    return _TOKENISH.sub("<hidden>", s)


def load_dotenv_file() -> None:
    """Load KEY=VALUE lines from <config dir>/.env into the environment (without overriding real env vars)."""
    p = config_dir() / ".env"
    if not p.is_file():
        return
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip("'\""))


def client_credentials() -> Tuple[str, str]:
    load_dotenv_file()
    cid, sec = os.environ.get("LINKEDIN_CLIENT_ID", ""), os.environ.get("LINKEDIN_CLIENT_SECRET", "")
    if not cid or not sec:
        raise SystemExit(
            "LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET are not set.\n"
            "Put them in your shell environment or in "
            f"{config_dir() / '.env'} (never in chat, never in a git repository).\n"
            "See docs/SETUP.md, step 4."
        )
    return cid, sec


# ---------------------------------------------------------------- token store
def token_path() -> Path:
    return config_dir() / "token.json"


def save_token(data: Dict[str, Any]) -> Path:
    d = config_dir()
    d.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(d, 0o700)
    except OSError:
        pass
    p = token_path()
    tmp = p.with_suffix(".tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump(data, f)
    os.replace(tmp, p)
    os.chmod(p, stat.S_IRUSR | stat.S_IWUSR)
    return p


def load_token(required: bool = True) -> Optional[Dict[str, Any]]:
    p = token_path()
    if not p.is_file():
        if required:
            raise SystemExit("No saved login. Run: li-auth login")
        return None
    t = json.loads(p.read_text())
    if required and t.get("expires_at") and t["expires_at"] < datetime.now(timezone.utc).timestamp():
        raise SystemExit("Your LinkedIn login has expired (tokens last 60 days). Run: li-auth login")
    return t


def person_urn(token: Dict[str, Any]) -> str:
    u = token.get("person_urn")
    if not u:
        raise SystemExit("The saved login has no profile id. Run: li-auth login again.")
    return u


# ---------------------------------------------------------------- HTTP
class Reply:
    def __init__(self, status: int, headers: Dict[str, str], body: bytes):
        self.status, self.headers, self.body = status, headers, body

    @property
    def ok(self) -> bool:
        return 200 <= self.status < 300

    def json(self) -> Any:
        try:
            return json.loads(self.body.decode("utf8") or "null")
        except ValueError:
            return None

    def header(self, name: str) -> str:
        for k, v in self.headers.items():
            if k.lower() == name.lower():
                return v
        return ""


def http(method: str, url: str, headers: Optional[Dict[str, str]] = None, body: Optional[bytes] = None, timeout: int = 30) -> Reply:
    """One HTTP call. Never raises on an HTTP error status; returns the Reply."""
    req = urllib.request.Request(url, data=body, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return Reply(r.status, dict(r.headers.items()), r.read())
    except urllib.error.HTTPError as e:
        return Reply(e.code, dict(e.headers.items()) if e.headers else {}, e.read() or b"")
    except urllib.error.URLError as e:
        raise SystemExit(f"Could not reach LinkedIn: {redact(e.reason)}")


def rest_headers(access_token: str, content_type: Optional[str] = "application/json") -> Dict[str, str]:
    h = {
        "Authorization": f"Bearer {access_token}",
        "X-Restli-Protocol-Version": "2.0.0",
        "Linkedin-Version": api_version(),
    }
    if content_type:
        h["Content-Type"] = content_type
    return h


def explain_error(r: Reply) -> str:
    """A plain-English reason for a failed call (branches on the status, never on LinkedIn's message text)."""
    hint = {
        400: "The request was malformed (often a wrongly encoded URN or a bad field).",
        401: "The login is missing, expired or was revoked. Run: li-auth login",
        403: "This login is not allowed to do that (missing product/permission, or no role on that Page).",
        404: "Nothing found at that address or for that id.",
        409: "A write conflict. Try again.",
        422: "LinkedIn understood the request but cannot process it.",
        426: "The API version in use has been retired. Set LINKEDIN_API_VERSION to a newer one.",
        429: "A rate limit was hit (limits reset at midnight UTC). Try again later.",
    }.get(r.status, "LinkedIn had a problem on its side. Try again later." if r.status >= 500 else "Unexpected answer.")
    rid = r.header("x-li-request-id")
    return f"HTTP {r.status}. {hint}" + (f" (LinkedIn request id: {rid})" if rid else "")


# ---------------------------------------------------------------- daily call ledger (UTC day, like LinkedIn's limits)
def _ledger_path() -> Path:
    return config_dir() / "usage.json"


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def calls_today() -> int:
    p = _ledger_path()
    try:
        return int(json.loads(p.read_text()).get(_today(), 0))
    except (OSError, ValueError):
        return 0


def record_call(n: int = 1) -> None:
    p = _ledger_path()
    try:
        data = json.loads(p.read_text())
    except (OSError, ValueError):
        data = {}
    data = {k: v for k, v in data.items() if k >= _today()[:8] + "00" or k == _today()}   # keep this month only
    data[_today()] = int(data.get(_today(), 0)) + n
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data))


def budget_left(cap: int = DEFAULT_BUDGET) -> int:
    return max(0, cap - calls_today())
