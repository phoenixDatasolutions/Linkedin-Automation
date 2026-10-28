import os
import tempfile
from contextlib import contextmanager


@contextmanager
def private_home():
    """A throwaway config folder so tests never touch real credentials."""
    with tempfile.TemporaryDirectory() as d:
        old = {k: os.environ.get(k) for k in ("LINKEDIN_AUTOMATION_HOME", "LINKEDIN_CLIENT_ID", "LINKEDIN_CLIENT_SECRET", "LI_SECRETSCAN_EXTRA")}
        os.environ["LINKEDIN_AUTOMATION_HOME"] = d
        for k in ("LINKEDIN_CLIENT_ID", "LINKEDIN_CLIENT_SECRET", "LI_SECRETSCAN_EXTRA"):
            os.environ.pop(k, None)
        try:
            yield d
        finally:
            for k, v in old.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v


class FakeHttp:
    """Records calls and answers from a queue of (status, headers, body) tuples."""
    def __init__(self, replies):
        from linkedin_automation.common import Reply
        self.Reply, self.calls, self.replies = Reply, [], list(replies)

    def __call__(self, method, url, headers=None, body=None, timeout=30):
        self.calls.append({"method": method, "url": url, "headers": headers or {}, "body": body})
        status, hdrs, data = self.replies.pop(0)
        return self.Reply(status, hdrs, data if isinstance(data, bytes) else data.encode())
