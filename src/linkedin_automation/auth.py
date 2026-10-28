"""li-auth: sign in to LinkedIn with OAuth 2.0 (authorization code flow) and keep the token safely.

    li-auth setup     store your client id and secret privately (hidden input)
    li-auth check     show what is configured (never prints secrets)
    li-auth login     open LinkedIn, approve, save a 60-day token in a private file
    li-auth status    who is signed in and when it expires
    li-auth logout    delete the saved token
"""
from __future__ import annotations

import argparse
import http.server as httpserver
import json
import secrets
import socketserver
import time
import urllib.parse
import webbrowser
from datetime import datetime, timezone
from typing import Dict, Optional

from . import common
from .common import OAUTH_BASE, client_credentials, config_dir, http, load_token, redact, save_token

DEFAULT_SCOPES = "openid profile w_member_social"
DEFAULT_REDIRECT = "http://localhost:8765/callback"


def authorize_url(client_id: str, redirect_uri: str, scopes: str, state: str) -> str:
    q = urllib.parse.urlencode({
        "response_type": "code", "client_id": client_id, "redirect_uri": redirect_uri,
        "state": state, "scope": scopes,
    })
    return f"{OAUTH_BASE}/authorization?{q}"


def parse_redirect(url_or_query: str) -> Dict[str, str]:
    """Pull code/state/error out of a full redirect URL or a bare query string."""
    q = urllib.parse.urlparse(url_or_query.strip()).query or url_or_query.strip().lstrip("?")
    return {k: v[0] for k, v in urllib.parse.parse_qs(q).items()}


def exchange_code(code: str, client_id: str, client_secret: str, redirect_uri: str) -> Dict:
    body = urllib.parse.urlencode({
        "grant_type": "authorization_code", "code": code, "client_id": client_id,
        "client_secret": client_secret, "redirect_uri": redirect_uri,
    }).encode()
    r = http("POST", f"{OAUTH_BASE}/accessToken", {"Content-Type": "application/x-www-form-urlencoded"}, body)
    if not r.ok:
        raise SystemExit(f"LinkedIn would not exchange the code. {common.explain_error(r)}\n"
                         "Typical causes: the code is older than 30 minutes or was used before, or the redirect URL "
                         "is not exactly the one registered on the app.")
    return r.json()


def fetch_person_urn(access_token: str) -> Optional[str]:
    """OpenID userinfo: `sub` is the member id, which makes the person URN."""
    r = http("GET", f"{common.API_BASE}/v2/userinfo", {"Authorization": f"Bearer {access_token}"})
    if r.ok and r.json() and r.json().get("sub"):
        return f"urn:li:person:{r.json()['sub']}"
    return None


class _Catcher(httpserver.BaseHTTPRequestHandler):
    result: Dict[str, str] = {}

    def do_GET(self):  # noqa: N802
        _Catcher.result = parse_redirect(self.path)
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"<h2>LinkedIn login received.</h2><p>You can close this tab and go back to the terminal.</p>")

    def log_message(self, *a):  # silence request logging (it would contain the code)
        pass


def _wait_for_redirect(port: int, timeout: int) -> Dict[str, str]:
    """Listen on localhost for LinkedIn's redirect. Returns {} if the port is busy or nothing arrives in time."""
    _Catcher.result = {}
    socketserver.TCPServer.allow_reuse_address = True
    try:
        srv = socketserver.TCPServer(("127.0.0.1", port), _Catcher)
    except OSError:
        return {}
    srv.timeout = 1
    end = time.time() + timeout
    try:
        while time.time() < end and not _Catcher.result:
            srv.handle_request()
    finally:
        srv.server_close()
    return _Catcher.result


def login(scopes: str, redirect_uri: str, manual: bool, timeout: int = 180, open_browser: bool = True) -> None:
    cid, secret = client_credentials()
    state = secrets.token_urlsafe(24)
    url = authorize_url(cid, redirect_uri, scopes, state)
    print("1) Open this address in your browser and approve access:\n")
    print(url + "\n")
    if open_browser and not manual:
        try:
            webbrowser.open(url)
        except Exception:
            pass
    got: Dict[str, str] = {}
    parsed = urllib.parse.urlparse(redirect_uri)
    if not manual and parsed.hostname in ("localhost", "127.0.0.1") and parsed.scheme == "http":
        print(f"2) Waiting up to {timeout}s for LinkedIn to send you back to {redirect_uri} ...")
        got = _wait_for_redirect(parsed.port or 80, timeout)
    if not got:
        print("2) After approving, your browser goes to the redirect address. Copy the WHOLE address from the\n"
              "   browser's address bar (even if the page shows an error) and paste it here.")
        got = parse_redirect(input("   Redirect address: "))
    if got.get("error"):
        raise SystemExit(f"LinkedIn refused: {redact(got.get('error'))} - {redact(got.get('error_description', ''))}")
    if got.get("state") != state:
        raise SystemExit("The 'state' did not match, so the login was rejected (possible forged request). Start again.")
    if not got.get("code"):
        raise SystemExit("No code found in what was pasted. Start again.")
    tok = exchange_code(got["code"], cid, secret, redirect_uri)
    now = datetime.now(timezone.utc).timestamp()
    data = {
        "access_token": tok["access_token"],
        "expires_at": now + int(tok.get("expires_in", 5184000)),
        "scope": tok.get("scope", scopes),
        "created_at": now,
    }
    if tok.get("refresh_token"):
        data["refresh_token"] = tok["refresh_token"]
        data["refresh_expires_at"] = now + int(tok.get("refresh_token_expires_in", 0))
    data["person_urn"] = fetch_person_urn(tok["access_token"])
    path = save_token(data)
    print(f"\nSigned in. Token saved privately to {path} (owner-only). It is valid for about "
          f"{int(tok.get('expires_in', 5184000)) // 86400} days.")
    print(f"Signed in as: {data['person_urn'] or '(profile id not available: add the OpenID product and the openid/profile scopes)'}")


def cmd_check() -> int:
    common.load_dotenv_file()
    import os
    rows = [
        ("LINKEDIN_CLIENT_ID", bool(os.environ.get("LINKEDIN_CLIENT_ID"))),
        ("LINKEDIN_CLIENT_SECRET", bool(os.environ.get("LINKEDIN_CLIENT_SECRET"))),
    ]
    for k, ok in rows:
        print(f"{'OK ' if ok else 'MISSING'}  {k}")
    t = load_token(required=False)
    print(f"{'OK ' if t else 'none'}  saved login ({common.token_path()})")
    print(f"      API version header: {common.api_version()}")
    print(f"      calls made today (UTC): {common.calls_today()} of {common.MEMBER_DAILY_LIMIT} allowed per member")
    return 0 if all(ok for _, ok in rows) else 1


def cmd_setup() -> int:
    """Ask for the client id and secret with hidden input and store them privately. Nothing is echoed or logged."""
    import getpass
    d = config_dir()
    d.mkdir(parents=True, exist_ok=True)
    try:
        import os as _os
        _os.chmod(d, 0o700)
    except OSError:
        pass
    print("Paste the values from your LinkedIn app's Auth tab. The secret is hidden while you type.")
    cid = input("Client ID: ").strip()
    secret = getpass.getpass("Client Secret (hidden): ").strip()
    if not cid or not secret:
        raise SystemExit("Both are needed. Nothing was saved.")
    envp = d / ".env"
    import os as _os
    fd = _os.open(envp, _os.O_WRONLY | _os.O_CREAT | _os.O_TRUNC, 0o600)
    with _os.fdopen(fd, "w") as f:
        f.write(f"LINKEDIN_CLIENT_ID={cid}\nLINKEDIN_CLIENT_SECRET={secret}\n")
    print(f"Saved to {envp} (owner-only). Next: li-auth login")
    return 0


def cmd_status() -> int:
    t = load_token(required=False)
    if not t:
        print("Not signed in. Run: li-auth login")
        return 1
    left = t.get("expires_at", 0) - datetime.now(timezone.utc).timestamp()
    print(f"Signed in as: {t.get('person_urn')}")
    print(f"Scopes: {t.get('scope')}")
    print("Expires: " + (f"in {left / 86400:.0f} days" if left > 0 else "EXPIRED - run: li-auth login"))
    return 0 if left > 0 else 1


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="li-auth", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check", help="show what is configured")
    l = sub.add_parser("login", help="sign in and save a token")
    l.add_argument("--scopes", default=DEFAULT_SCOPES, help=f"space separated (default: {DEFAULT_SCOPES})")
    l.add_argument("--redirect", default=DEFAULT_REDIRECT, help="must match a redirect URL registered on the app")
    l.add_argument("--manual", action="store_true", help="do not start a local listener; paste the redirect address instead")
    l.add_argument("--no-browser", action="store_true")
    sub.add_parser("setup", help="store your client id and secret privately (hidden input)")
    sub.add_parser("status", help="show who is signed in")
    sub.add_parser("logout", help="delete the saved token")
    a = p.parse_args(argv)
    if a.cmd == "check":
        return cmd_check()
    if a.cmd == "setup":
        return cmd_setup()
    if a.cmd == "status":
        return cmd_status()
    if a.cmd == "logout":
        pth = common.token_path()
        if pth.exists():
            pth.unlink()
            print("Saved login deleted.")
        else:
            print("Nothing to delete.")
        return 0
    login(a.scopes, a.redirect, a.manual, open_browser=not a.no_browser)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
