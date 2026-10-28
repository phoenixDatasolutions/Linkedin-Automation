import json
import os
import stat
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))

from helpers import FakeHttp, private_home
from linkedin_automation import auth, common, littletext, post


class LittleText(unittest.TestCase):
    def test_reserved_characters_are_escaped(self):
        self.assertEqual(littletext.escape("a_b*c (x) [y] {z} | ~ @ <>"), r"a\_b\*c \(x\) \[y\] \{z\} \| \~ \@ \<\>")

    def test_hashtags_stay_clickable(self):
        self.assertEqual(littletext.escape("Learn #Python today"), "Learn #Python today")

    def test_mention(self):
        self.assertEqual(littletext.mention("Acme (UK)", "urn:li:organization:1"), r"@[Acme \(UK\)](urn:li:organization:1)")


class Payloads(unittest.TestCase):
    A = "urn:li:person:abc"

    def test_text_post_shape(self):
        p = post.base_post(self.A, "Hello")
        self.assertEqual((p["author"], p["lifecycleState"], p["visibility"]), (self.A, "PUBLISHED", "PUBLIC"))
        self.assertEqual(p["distribution"]["feedDistribution"], "MAIN_FEED")

    def test_bad_visibility(self):
        with self.assertRaises(SystemExit):
            post.base_post(self.A, "x", "EVERYONE")

    def test_one_image_vs_many(self):
        one = post.with_images(post.base_post(self.A, "x"), ["urn:li:image:1"], "alt")
        self.assertEqual(one["content"]["media"], {"id": "urn:li:image:1", "altText": "alt"})
        many = post.with_images(post.base_post(self.A, "x"), ["urn:li:image:1", "urn:li:image:2"])
        self.assertEqual(len(many["content"]["multiImage"]["images"]), 2)
        with self.assertRaises(SystemExit):
            post.with_images(post.base_post(self.A, "x"), [f"urn:li:image:{i}" for i in range(21)])

    def test_poll_limits(self):
        ok = post.with_poll(post.base_post(self.A, "x"), "Q?", ["a", "b"], 3)
        self.assertEqual(ok["content"]["poll"]["settings"]["duration"], "THREE_DAYS")
        for bad in (("Q" * 141, ["a", "b"], 3), ("Q?", ["a"], 3), ("Q?", ["a", "b"], 5), ("Q?", ["x" * 31, "b"], 3)):
            with self.assertRaises(SystemExit):
                post.with_poll(post.base_post(self.A, "x"), *bad)

    def test_document_and_article(self):
        d = post.with_document(post.base_post(self.A, "x"), "urn:li:document:1", "Title")
        self.assertEqual(d["content"]["media"], {"title": "Title", "id": "urn:li:document:1"})
        a = post.with_article(post.base_post(self.A, "x"), "https://e.com", "T", "D", "urn:li:image:9")
        self.assertEqual(a["content"]["article"]["thumbnail"], "urn:li:image:9")

    def test_comment_body(self):
        self.assertEqual(post.comment_body(self.A, "urn:li:share:1", "hi_there")["message"]["text"], r"hi\_there")


class Secrets(unittest.TestCase):
    def test_token_file_is_private_and_never_printed(self):
        with private_home() as d:
            p = common.save_token({"access_token": "AQ" + "k" * 120, "expires_at": 9999999999, "person_urn": "urn:li:person:x"})
            self.assertEqual(stat.S_IMODE(os.stat(p).st_mode), 0o600)
            self.assertEqual(stat.S_IMODE(os.stat(d).st_mode), 0o700)
            self.assertNotIn("AQ" + "k" * 20, common.redact(json.dumps(common.load_token())))

    def test_redact(self):
        os.environ["LINKEDIN_CLIENT_SECRET"] = "supersecretvalue123"
        try:
            s = common.redact("x supersecretvalue123 Authorization: Bearer abcdefghijklmnopqrstuvwxyz client_secret=abc123")
            self.assertNotIn("supersecretvalue123", s)
            self.assertNotIn("abcdefghijklmnopqrstuvwxyz", s)
            self.assertNotIn("abc123", s)
        finally:
            os.environ.pop("LINKEDIN_CLIENT_SECRET")

    def test_expired_login_is_refused(self):
        with private_home():
            common.save_token({"access_token": "t", "expires_at": 1, "person_urn": "urn:li:person:x"})
            with self.assertRaises(SystemExit):
                common.load_token()

    def test_ledger_counts_per_day(self):
        with private_home():
            self.assertEqual(common.calls_today(), 0)
            common.record_call(); common.record_call(3)
            self.assertEqual(common.calls_today(), 4)
            self.assertEqual(common.budget_left(10), 6)


class Login(unittest.TestCase):
    def test_authorize_url_has_state_and_scopes(self):
        u = auth.authorize_url("cid", "http://localhost:8765/callback", "openid profile w_member_social", "STATE")
        self.assertIn("state=STATE", u)
        self.assertIn("scope=openid+profile+w_member_social", u)
        self.assertIn("response_type=code", u)

    def test_parse_redirect(self):
        self.assertEqual(auth.parse_redirect("http://localhost:8765/callback?code=c1&state=s1"), {"code": "c1", "state": "s1"})
        self.assertEqual(auth.parse_redirect("?error=user_cancelled_authorize"), {"error": "user_cancelled_authorize"})

    def _login(self, state_in_redirect):
        os.environ["LINKEDIN_CLIENT_ID"], os.environ["LINKEDIN_CLIENT_SECRET"] = "cid", "secret-value-1234"
        fake = FakeHttp([(200, {}, json.dumps({"access_token": "AQ" + "z" * 80, "expires_in": 5184000, "scope": "openid profile w_member_social"})),
                         (200, {}, json.dumps({"sub": "member123"}))])
        auth.http = fake
        captured = {}
        orig_url = auth.authorize_url
        auth.authorize_url = lambda *a: (captured.setdefault("state", a[3]), orig_url(*a))[1]
        auth.input = lambda prompt="": f"http://localhost:8765/callback?code=thecode&state={state_in_redirect or captured['state']}"
        try:
            auth.login("openid profile w_member_social", "http://localhost:8765/callback", manual=True, open_browser=False)
        finally:
            auth.authorize_url = orig_url
            del auth.input
        return fake

    def test_login_saves_token_and_person(self):
        with private_home():
            fake = self._login(None)
            t = common.load_token()
            self.assertEqual(t["person_urn"], "urn:li:person:member123")
            self.assertIn("client_secret=secret-value-1234", fake.calls[0]["body"].decode())   # secret goes in the body, not the URL  # secretscan:allow
            self.assertNotIn("secret", fake.calls[0]["url"])

    def test_wrong_state_is_rejected(self):
        with private_home():
            with self.assertRaises(SystemExit):
                self._login("FORGED")
            self.assertIsNone(common.load_token(required=False))


class Publishing(unittest.TestCase):
    def setUp(self):
        self._http = post.http

    def tearDown(self):
        post.http = self._http

    def _signed_in(self):
        common.save_token({"access_token": "AQ" + "t" * 100, "expires_at": 9999999999, "person_urn": "urn:li:person:me"})

    def test_dry_run_sends_nothing(self):
        with private_home():
            post.http = FakeHttp([])   # any call would pop from an empty list and fail
            self.assertEqual(post.main(["text", "A quiet, honest note about reports.", "--no-lint"]), 0)

    def test_publish_requires_confirmation_when_not_interactive(self):
        with private_home():
            self._signed_in()
            post.http = FakeHttp([])
            with self.assertRaises(SystemExit):
                post.main(["text", "Hello there", "--no-lint", "--publish"])

    def test_text_publish_headers_and_result(self):
        with private_home():
            self._signed_in()
            fake = post.http = FakeHttp([(201, {"x-restli-id": "urn:li:share:777"}, b"")])
            self.assertEqual(post.main(["text", "Hello there", "--no-lint", "--publish", "--yes"]), 0)
            c = fake.calls[0]
            self.assertEqual((c["method"], c["url"]), ("POST", "https://api.linkedin.com/rest/posts"))
            self.assertEqual(c["headers"]["X-Restli-Protocol-Version"], "2.0.0")
            self.assertRegex(c["headers"]["Linkedin-Version"], r"^\d{6}$")
            self.assertEqual(json.loads(c["body"])["author"], "urn:li:person:me")
            self.assertEqual(common.calls_today(), 1)

    def test_image_upload_sequence(self):
        import tempfile
        with private_home():
            self._signed_in()
            with tempfile.NamedTemporaryFile(suffix=".png") as img:
                img.write(b"\x89PNG....")
                img.flush()
                fake = post.http = FakeHttp([
                    (200, {}, json.dumps({"value": {"uploadUrl": "https://www.linkedin.com/dms-uploads/x", "image": "urn:li:image:IMG1"}})),
                    (201, {}, b""),
                    (201, {"x-restli-id": "urn:li:share:8"}, b""),
                ])
                self.assertEqual(post.main(["image", "Caption here", img.name, "--no-lint", "--publish", "--yes"]), 0)
            self.assertEqual([c["method"] for c in fake.calls], ["POST", "PUT", "POST"])
            self.assertIn("action=initializeUpload", fake.calls[0]["url"])
            self.assertTrue(fake.calls[1]["headers"]["Authorization"].startswith("Bearer "))   # the image PUT carries the token
            self.assertEqual(json.loads(fake.calls[2]["body"])["content"]["media"]["id"], "urn:li:image:IMG1")

    def test_first_comment(self):
        with private_home():
            self._signed_in()
            fake = post.http = FakeHttp([(201, {"x-restli-id": "urn:li:share:5"}, b""), (201, {}, b"")])
            post.main(["text", "Hello there", "--no-lint", "--publish", "--yes", "--first-comment", "Link: https://e.com"])
            self.assertIn("/socialActions/urn%3Ali%3Ashare%3A5/comments", fake.calls[1]["url"])

    def test_failed_publish_explains_without_leaking_token(self):
        with private_home():
            self._signed_in()
            post.http = FakeHttp([(403, {"x-li-request-id": "REQ1"}, b'{"message":"nope Bearer AQ' + b"q" * 90 + b'"}')])
            with self.assertRaises(SystemExit) as cm:
                post.main(["text", "Hello there", "--no-lint", "--publish", "--yes"])
            self.assertIn("403", str(cm.exception))
            self.assertNotIn("q" * 30, str(cm.exception))


if __name__ == "__main__":
    unittest.main()
