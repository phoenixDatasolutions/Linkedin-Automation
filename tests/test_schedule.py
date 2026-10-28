import json
import os
import sys
import unittest
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))

from helpers import FakeHttp, private_home
from linkedin_automation import auth, common, post, schedule

TEXT = "Our month-end close used to take three days.\n\nNow it takes one afternoon, because the data model is clean.\n\n#Finance #Analytics"


class Schedule(unittest.TestCase):
    def setUp(self):
        self._http = post.http

    def tearDown(self):
        post.http = self._http

    def _login(self):
        common.save_token({"access_token": "AQ" + "t" * 100, "expires_at": 9999999999, "person_urn": "urn:li:person:me"})

    def _due(self, minutes=-5):
        return datetime.now(timezone.utc) + timedelta(minutes=minutes)

    def test_timezone_conversion(self):
        self.assertEqual(schedule.parse_local("2026-11-03 09:30", "Asia/Kolkata").strftime("%H:%M"), "04:00")
        with self.assertRaises(SystemExit):
            schedule.parse_local("tomorrow", None)

    def test_unapproved_posts_never_publish(self):
        with private_home():
            self._login()
            post.http = FakeHttp([])        # any publish attempt would fail the test
            schedule.add(TEXT, self._due(), [], None, "PUBLIC")
            self.assertEqual(schedule.run(), ["Nothing due."])

    def test_approved_due_post_is_published_once(self):
        with private_home():
            self._login()
            fake = post.http = FakeHttp([(201, {"x-restli-id": "urn:li:share:42"}, b"")])
            item = schedule.add(TEXT, self._due(), [], None, "PUBLIC")
            i = schedule.load(item["id"]); i["status"] = "approved"; schedule.save(i)
            self.assertIn("published", schedule.run()[0])
            self.assertEqual(schedule.load(item["id"])["status"], "sent")
            self.assertEqual(schedule.run(), ["Nothing due."])          # second run does nothing
            self.assertEqual(len(fake.calls), 1)

    def test_future_posts_wait(self):
        with private_home():
            self._login()
            post.http = FakeHttp([])
            item = schedule.add(TEXT, self._due(+60), [], None, "PUBLIC")
            i = schedule.load(item["id"]); i["status"] = "approved"; schedule.save(i)
            self.assertEqual(schedule.run(), ["Nothing due."])

    def test_failure_is_recorded_and_not_retried(self):
        with private_home():
            self._login()
            fake = post.http = FakeHttp([(403, {}, b"{}")])
            item = schedule.add(TEXT, self._due(), [], None, "PUBLIC")
            i = schedule.load(item["id"]); i["status"] = "approved"; schedule.save(i)
            self.assertIn("FAILED", schedule.run()[0])
            self.assertEqual(schedule.load(item["id"])["status"], "failed")
            self.assertEqual(schedule.run(), ["Nothing due."])
            self.assertEqual(len(fake.calls), 1)

    def test_daily_cap(self):
        with private_home():
            self._login()
            replies = [(201, {"x-restli-id": f"urn:li:share:{n}"}, b"") for n in range(5)]
            fake = post.http = FakeHttp(replies)
            for n in range(3):
                item = schedule.add(TEXT + f" {n}", self._due(-10 + n), [], None, "PUBLIC")
                i = schedule.load(item["id"]); i["status"] = "approved"; schedule.save(i)
            out = schedule.run()
            self.assertEqual(sum("published" in l for l in out), 2)
            self.assertTrue(any("daily cap" in l for l in out))
            self.assertEqual(len(fake.calls), 2)

    def test_bad_posts_are_not_queued(self):
        with private_home():
            with self.assertRaises(SystemExit):
                schedule.add("x" * 3100, self._due(), [], None, "PUBLIC")


class AuthSetup(unittest.TestCase):
    def test_setup_writes_private_env_without_echo(self):
        import getpass, stat
        with private_home() as d:
            old_in, old_gp = __builtins__["input"] if isinstance(__builtins__, dict) else __builtins__.input, getpass.getpass
            auth.input = lambda p="": "my-client-id"
            getpass.getpass = lambda p="": "my-secret-value-123"
            try:
                self.assertEqual(auth.cmd_setup(), 0)
            finally:
                del auth.input
                getpass.getpass = old_gp
            env = os.path.join(d, ".env")
            self.assertEqual(stat.S_IMODE(os.stat(env).st_mode), 0o600)
            common.load_dotenv_file()
            self.assertEqual(os.environ["LINKEDIN_CLIENT_SECRET"], "my-secret-value-123")
            os.environ.pop("LINKEDIN_CLIENT_ID", None); os.environ.pop("LINKEDIN_CLIENT_SECRET", None)

    def test_delete_post_dry_run_and_call(self):
        with private_home():
            common.save_token({"access_token": "AQ" + "t" * 100, "expires_at": 9999999999, "person_urn": "urn:li:person:me"})
            fake = post.http = FakeHttp([(204, {}, b"")])
            try:
                self.assertEqual(post.main(["delete", "urn:li:share:9"]), 0)
                self.assertEqual(fake.calls, [])
                self.assertEqual(post.main(["delete", "urn:li:share:9", "--publish", "--yes"]), 0)
                self.assertEqual(fake.calls[0]["method"], "DELETE")
                self.assertTrue(fake.calls[0]["url"].endswith("/rest/posts/urn%3Ali%3Ashare%3A9"))
            finally:
                post.http = common.http


if __name__ == "__main__":
    unittest.main()
