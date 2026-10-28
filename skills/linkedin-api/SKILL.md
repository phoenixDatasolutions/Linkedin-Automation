---
name: linkedin-api
description: Expert reference for the official LinkedIn API (docs snapshot 2026-10-29, API version 202610). Use for any question about LinkedIn OAuth and tokens, getting API access or an "API key", posting to LinkedIn programmatically (Posts API, images, documents, polls, comments, reactions), post and page analytics, Community Management tiers and rate limits, API versions and error codes, webhooks, data-storage and AI-use rules, plus a map of Ads, Lead Sync, Conversions, Learning, Sales Navigator, Talent and Compliance APIs.
---

# LinkedIn API knowledge

Distilled from the whole of https://learn.microsoft.com/en-us/linkedin/ (about 580 pages read on 2026-10-28/29), written in original words with the source page named in every file. LinkedIn changes this API every month, so treat numbers, limits and permission names as "true on 2026-10-29" and re-check the linked page before relying on anything that costs money, risks an account or ships to production.

## How to use this skill
1. Find the topic in the table, open that one file in `references/` (never load them all).
2. Tell the user which documentation page a fact came from.
3. If something is not covered, search `references/09-page-index.md` for the right page and read the live page. Say plainly when you could not verify.
4. Never ask the user to paste a client secret, token or password into the chat. Credentials go into their own terminal (`li-auth setup`).

| Question about... | Open |
|---|---|
| Getting access, "API key", products, scopes, OAuth flows, tokens, refresh, secrets, tiers | `references/01-access-and-auth.md` |
| Request format: base URLs, headers, Rest.li 2.0 encoding, versions, methods, errors, rate limits, webhooks | `references/02-api-mechanics.md` |
| Posting and engagement: text, image, multi-image, video, document, poll, article, reshare, edit, delete, mentions, comments, reactions | `references/03-posting-and-engagement.md` |
| Analytics: post/profile/page/follower/video numbers, notifications | `references/04-analytics.md` |
| Sign in with LinkedIn, Share on LinkedIn, plugins, Verified, Live | `references/05-sign-in-and-share.md` |
| What is allowed: restricted uses, data storage limits, AI policy, app review, Development vs Standard tier | `references/06-rules-and-policies.md` |
| Ads, Lead Sync, Conversions, Matched Audiences, Events, Learning, Sales Navigator, Talent, Compliance | `references/07-other-programs.md` |
| Something is failing | `references/08-troubleshooting.md` |
| "Where is the page about X?" | `references/09-page-index.md` |
| Version table, sunsets, recent changes, legacy-to-new API map | `references/10-versions-and-changes.md` |

## Ten facts that decide most questions
1. **There is no "LinkedIn API key".** You create a developer *app* (client ID + client secret), then each person signs in with OAuth 2.0 and the app receives an access token (60 days).
2. **Fastest path to posting from your own software:** add the open products "Share on LinkedIn" (`w_member_social`) and "Sign in with LinkedIn using OpenID Connect" (`openid profile`) to an app. No review needed.
3. **Reading post numbers** needs the Community Management API (scope `r_member_postAnalytics`): reviewed, Development tier first, and it **must be the only product on its own app**.
4. **Two base paths:** `https://api.linkedin.com/rest/` (versioned, needs `Linkedin-Version: YYYYMM` and `X-Restli-Protocol-Version: 2.0.0`) and the older `/v2/`. Latest version is `202610`; each version lives 12 months.
5. **Development tier limits:** 500 calls/app/day and 100 calls/member/day, no BATCH_GET, 12 months to apply for Standard or access is removed. Limits reset at midnight UTC.
6. **Member post analytics is one post and one metric per call.** No batching. Page (organization) share statistics can take several posts in one call.
7. **Reading other people's posts or comments is not possible** (`r_member_social` is closed to everyone).
8. **Posting returns 201 with an empty body;** the new post id is in the `x-restli-id` header.
9. **Stored data has clocks:** members' social activity 48 hours, other members' profile data 24 hours, Page reporting data one year.
10. **AI rules:** LinkedIn recommends no automated posting of AI-written content without a person involved and prohibits using API-retrieved member content as AI input except in narrow cases. Build an approval step. See `references/06-rules-and-policies.md`.

## Related skills in this toolkit
`linkedin-api-setup` (guided credentials), `linkedin-publisher` (post with approval), `linkedin-writer`, `linkedin-post-check`, `linkedin-comments`, `linkedin-planner`, `linkedin-analytics`.
