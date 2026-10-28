---
name: linkedin-analytics
description: Read and interpret LinkedIn post numbers (views, reactions, comments, reposts, followers) through the official analytics API while staying inside the daily call limit, and turn them into decisions. Use for "how did my LinkedIn post do", "LinkedIn analytics", "which posts perform", "check my impressions", or when API calls hit rate limits (429).
---

# LinkedIn analytics

Needs the Community Management API (`r_member_postAnalytics`) on its own developer app. See `linkedin-api-setup` step 9. Command: `li-stats`.

## The one fact that shapes everything
LinkedIn answers **one post and one metric per call**, and the Development tier allows **100 calls per member per day** (500 per app). There is no batch. So:
- 10 posts x 3 metrics = 30 calls. Plan for it.
- `li-stats` keeps a local call counter, caches answers for 6 hours and stops at 90 calls by default.

## Commands
```bash
li-stats budget                                   # calls used today vs the limit
li-stats post urn:li:share:123                    # IMPRESSION, REACTION, COMMENT, RESHARE (4 calls)
li-stats post urn:li:share:123 --metrics IMPRESSION   # just views (1 call)
li-stats me --metric IMPRESSION --days 30         # ONE call: total views across all posts in 30 days
li-stats me --metric IMPRESSION --days 30 --daily # ONE call: per-day series across all posts
li-stats followers                                # follower count (needs r_member_profileAnalytics)
li-stats post URN --fresh                         # ignore the cache
```
Metrics available: IMPRESSION, MEMBERS_REACHED, REACTION, COMMENT, RESHARE, and from API version 202604 POST_SAVE, POST_SEND, LINK_CLICKS, PREMIUM_CTA_CLICKS, FOLLOWER_GAINED_FROM_CONTENT, PROFILE_VIEW_FROM_CONTENT.

## Spend calls wisely
| Post age | How often | Metrics |
|---|---|---|
| 0-7 days | every few hours at most | IMPRESSION first; add REACTION/COMMENT/RESHARE only if views > 0 |
| 8-30 days | once a day | IMPRESSION |
| older | weekly or never | numbers barely move |
Use the `me` finder for trends (one call for everything) and the `entity` finder only for the posts you want to study. Never poll in a loop and never refresh on program start-up.

## Reading the numbers
- **Impressions** = times shown; **members reached** = unique people. Reach below impressions means repeat views.
- **Engagement rate** = (reactions + comments + reposts) / impressions. Compare posts of similar age; a 2-day-old post is not comparable with a 30-day-old one.
- Comments and reposts matter more than reactions. Saves and link clicks (202604+) show real usefulness.
- Numbers are "best effort, not for billing", and the `me` totals for reactions/comments/reposts may not match the LinkedIn app exactly (the docs say so).
- Small samples lie: judge formats and hooks over at least 5-8 posts, not one.

## Decisions to make from it
1. Top two posts last month: what do they share (topic, format, first line, time)? Do more of that.
2. Bottom two: fix the hook first (it decides most of the result).
3. Followers gained from content (202604+): which posts brought followers, not just views?
4. Update `PLAN.md` (see `linkedin-planner`) with one change for next month.

## Storage and privacy
Your own numbers are yours, but LinkedIn limits how long some data may be stored (members' social activity 48 hours; Page reporting data one year). Keep a summary, not raw member data, and read `linkedin-api/references/06-rules-and-policies.md` before building a long-term database.

## When you hit 429
You used the day's calls. Limits reset at midnight UTC. Check `li-stats budget`; lower the refresh rate; do not retry in a loop.
