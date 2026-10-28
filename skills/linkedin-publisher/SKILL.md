---
name: linkedin-publisher
description: Publish and schedule LinkedIn posts through the official API with a mandatory human approval step. Use when the user says "post this to LinkedIn", "publish", "schedule a LinkedIn post", "queue posts", "add a first comment", or wants an image, PDF carousel (document), poll or article post sent. Drafts first, runs the writing check, shows the exact payload, and only publishes after an explicit yes.
---

# LinkedIn publisher (approval first, always)

Uses the `li-post` and `li-schedule` commands from this toolkit. Prerequisite: `linkedin-api-setup` finished (`li-auth status` shows days left).

## The non-negotiable loop
1. **Draft** with `linkedin-writer` (or take the user's text).
2. **Check**: `li-lint --file post.txt` (or let `li-post` run it). Fix errors; discuss warnings.
3. **Show the user the final text, exactly as it will appear**, plus: visibility, any images/PDF, first comment, and when it will go out.
4. **Wait for an explicit yes in this conversation** ("approve", "post it", "yes publish"). Silence, a thumbs-up on an earlier draft, or a yes to an older version does **not** count. If the text changed after the yes, ask again.
5. **Publish**, then give the user the link and the call count.
Never publish on a schedule, from a loop, or in the background unless the user approved *that exact text* beforehand (see scheduling).

Why: LinkedIn's Developer AI Policy recommends against automated posting of AI-generated content without a person involved, and it is your user's name on the post.

## Commands (always dry-run first, it is the default)
```bash
li-post text "Post text" [--file post.txt] [--visibility PUBLIC|CONNECTIONS] [--first-comment "..."]
li-post image "Caption" a.png [b.png ...] [--alt "description"]      # 1 image, or 2-20 for a swipe gallery
li-post document "Caption" deck.pdf --title "Deck title"             # PDF/PPT/DOC carousel (max 100 MB, 300 pages)
li-post poll "Question (max 140)?" -o "A" -o "B" [-o "C" -o "D"] --days 3
li-post article "Caption" https://example.com --title "T" --description "D" [--thumbnail pic.png]
li-post delete urn:li:share:123 --publish                            # remove one of your own posts
```
Add `--publish` to send it. In a terminal the user must type the word `publish`. When *you* run it for them after their explicit yes, add `--yes`. Post as a Company Page with `--org <id>` (needs a Page role and `w_organization_social`).

Rules of thumb:
- Put links in the **first comment** (`--first-comment`), not the post body. Many writers do this; LinkedIn does not document a penalty, it is a habit.
- Always give images alt text (`--alt`).
- First real run: use `--visibility CONNECTIONS`, check it, then delete it.
- Posting returns 201 with an empty body; the tool prints the link from the `x-restli-id` header.
- Every image costs one or two extra API calls (register the upload, upload it). The tool prints the calls made today; the member limit is 100 a day on the Community Management Development tier (150 on the legacy Share product).

## Scheduling (LinkedIn's API has no "publish later")
The toolkit keeps its own queue. A person approves each item; a cron job publishes approved items when they are due.
```bash
li-schedule add post.txt --at "2026-11-03 09:30" --tz Europe/London [--image a.png] [--first-comment "..."]
li-schedule list
li-schedule approve <id>       # THE human yes - only run after the user said yes to this exact text
li-schedule run --dry-run      # what would go out now
li-schedule cron               # prints the crontab line (every 5 minutes)
```
Safety built in: unapproved items never publish; an item is marked "sending" before it is sent so a crash cannot double-post; failures are not retried; a daily cap (2 posts, `LI_SCHEDULE_DAILY_CAP`) stops runaway queues. `li-schedule cancel <id>` removes an item.

## What you must refuse or push back on
- Posting content you did not show the user, or text that changed after approval.
- Posting someone else's content, or reposting API-retrieved member content with AI changes.
- Mass posting, repeating the same post, engagement-bait pods, fake accounts, or scraping LinkedIn.
- Anything involving other people's private data.
Explain briefly why and offer the compliant alternative (see `linkedin-api/references/06-rules-and-policies.md`).

## If publishing fails
Read the one-line reason the tool prints (status code in plain words). 401 = sign in again; 403 = missing product/permission or no Page role; 429 = a daily limit, try tomorrow; 426 = set `LINKEDIN_API_VERSION` to a newer version. Full table: `linkedin-api/references/08-troubleshooting.md`.
