import json
import os
import sys
import unittest
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))

from helpers import FakeHttp, private_home
from linkedin_automation import common, lint, secretscan, stats

GOOD = """Our monthly report took 9 hours. Now it takes 40 minutes.

The change was boring: one clean data model, and every report reads from it.
Nobody has to copy numbers between files any more.

If your reports still start with "which file is the latest?", start there.

#PowerBI #Analytics #DataModeling"""


class Lint(unittest.TestCase):
    def test_good_post_is_clean_of_errors_and_warnings(self):
        r = lint.check(GOOD)
        self.assertEqual((r["errors"], r["warnings"]), ([], []))

    def test_ai_tells_and_bait(self):
        r = lint.check("I'm thrilled to announce a game-changer. Comment YES below!")
        text = " ".join(r["warnings"])
        self.assertIn("AI or a template", text)
        self.assertIn("Engagement bait", text)

    def test_word_variants_are_caught(self):
        r = lint.check("We unlocked the power of data by leveraging a seamless, revolutionising platform.")
        w = " ".join(r["warnings"])
        for needle in ("unlock the power", "leverage", "revolutionize", "seamless"):
            self.assertIn(needle, w)

    def test_hard_errors(self):
        self.assertTrue(lint.check("x" * 3001)["errors"])
        self.assertTrue(lint.check("Hello [Name], welcome")["errors"])
        self.assertTrue(lint.check("my token AQ" + "Tq8vN3kLm2PzR7wXc9Yb4HdJf6Gs1Ua5Eo0IiKtBnCeMlVhWyQxZrSgDpAfjUkLoN7")["errors"])
        self.assertTrue(lint.check("   ")["errors"])

    def test_hashtags_links_emoji_dashes(self):
        r = lint.check("Short. https://x.com — a — b — c #a #b #c #d #e #f \U0001F525\U0001F525\U0001F525\U0001F525")
        w = " ".join(r["warnings"])
        for needle in ("hashtags", "link", "emoji", "em dashes"):
            self.assertIn(needle, w)

    def test_cli_exit_codes(self):
        self.assertEqual(lint.main([GOOD]), 0)
        self.assertEqual(lint.main(["x" * 3001]), 1)


class Stats(unittest.TestCase):
    def setUp(self):
        self._http = stats.http

    def tearDown(self):
        stats.http = self._http

    def test_urls_match_the_documented_format(self):
        u = stats.post_url_query("urn:li:share:123", "IMPRESSION")
        self.assertIn("q=entity&entity=(share:urn%3Ali%3Ashare%3A123)&queryType=IMPRESSION&aggregation=TOTAL", u)
        self.assertIn("entity=(ugc:urn%3Ali%3AugcPost%3A9)", stats.post_url_query("urn:li:ugcPost:9", "COMMENT"))
        self.assertEqual(stats.date_range(datetime(2026, 5, 4), datetime(2026, 5, 6)), "(start:(day:4,month:5,year:2026),end:(day:6,month:5,year:2026))")
        self.assertIn("q=me&queryType=REACTION&aggregation=DAILY", stats.me_url_query("REACTION", True))

    def test_one_call_per_metric_then_cache(self):
        with private_home():
            fake = stats.http = FakeHttp([(200, {}, json.dumps({"elements": [{"count": 42}]}))])
            url = stats.post_url_query("urn:li:share:1", "IMPRESSION")
            a = stats.fetch("tok", url, 90)
            b = stats.fetch("tok", url, 90)
            self.assertEqual((a["count"], a["cached"], b["count"], b["cached"]), (42, False, 42, True))
            self.assertEqual(len(fake.calls), 1)
            self.assertEqual(common.calls_today(), 1)

    def test_stops_at_the_budget(self):
        with private_home():
            common.record_call(90)
            fake = stats.http = FakeHttp([])
            r = stats.fetch("tok", stats.post_url_query("urn:li:share:2", "COMMENT"), 90)
            self.assertFalse(r["ok"])
            self.assertIn("budget", r["error"])
            self.assertEqual(fake.calls, [])

    def test_429_is_explained(self):
        with private_home():
            stats.http = FakeHttp([(429, {}, b"{}")])
            r = stats.fetch("tok", stats.post_url_query("urn:li:share:3", "IMPRESSION"), 90)
            self.assertFalse(r["ok"])
            self.assertIn("midnight UTC", r["error"])


class SecretScan(unittest.TestCase):
    TOKEN = "AQ" + "Tq8vN3kLm2PzR7wXc9Yb4HdJf6Gs1Ua5Eo0IiKtBnCeMlVhWyQxZrSgDpAfjUkLoN7"

    def test_real_looking_secrets_are_found_without_printing_them(self):
        found = secretscan.scan_text(f"token = '{self.TOKEN}'\nLINKEDIN_CLIENT_SECRET=WPL_AP1.k3Jd9sLm2QpX7vNa\n", "f.txt")  # secretscan:allow
        self.assertEqual(len(found), 2)
        self.assertNotIn(self.TOKEN, " ".join(found))

    def test_placeholders_and_env_reads_are_fine(self):
        ok = ["LINKEDIN_CLIENT_SECRET=<your secret here>", "client_secret = os.environ['X']", "API_KEY=YOUR_API_KEY_HERE",
              'password: "xxxxxxxxxxxx"', "export LINKEDIN_CLIENT_ID=your-client-id"]
        self.assertEqual(secretscan.scan_text("\n".join(ok), "f"), [])

    def test_private_block_list_from_environment(self):
        with private_home():
            os.environ["LI_SECRETSCAN_EXTRA"] = "my-private-client-id-77"
            self.assertEqual(len(secretscan.scan_text("id is My-Private-Client-Id-77", "f", secretscan.extra_terms())), 1)


if __name__ == "__main__":
    unittest.main()
