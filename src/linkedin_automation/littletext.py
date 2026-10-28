"""LinkedIn's post text format ("little text").

The Posts API reads the post text as a single string in which a few characters have a special meaning
(mentions, hashtag templates, formatting). To show them as plain text they must be escaped with a backslash.
Reserved: | { } @ [ ] ( ) < > \\ * _ ~   and # when it is not a hashtag.
Hashtags are left alone on purpose so that "#python" stays a clickable hashtag.
"""
from __future__ import annotations

import re

_RESERVED = re.compile(r"([\\|{}@\[\]()<>*_~])")


def escape(text: str) -> str:
    """Escape plain text for the `commentary` field (hashtags stay clickable)."""
    return _RESERVED.sub(r"\\\1", text)


def mention(display_name: str, urn: str) -> str:
    """A real @mention. The display text must match the person's or company's name exactly (case sensitive)."""
    return f"@[{escape(display_name)}]({urn})"


def to_commentary(text: str) -> str:
    """Normalise line endings, trim, and escape."""
    return escape(text.replace("\r\n", "\n").strip())
