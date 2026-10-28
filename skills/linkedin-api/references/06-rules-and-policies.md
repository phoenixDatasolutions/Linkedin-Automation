# 06 - What you are allowed to do: terms, data limits, AI rules, access tiers

Sources (under `https://learn.microsoft.com/en-us/linkedin/`): `marketing/restricted-use-cases`, `marketing/data-storage-requirements`, `marketing/developer-ai-policy`, `marketing/community-management-app-review`, `marketing/increasing-access`, `marketing/lms-faq`, `marketing/tips-to-get-started`, `shared/breaking-change-policy`. Legal texts they point to: LinkedIn API Terms of Use, LinkedIn Marketing API Program Terms (https://www.linkedin.com/legal/l/marketing-api-terms), Plugin Terms.

> This file is a plain-language reading of LinkedIn's published pages. It is not legal advice. When a decision matters, read the live page and the linked terms. If a page and these notes disagree, the page wins.

## 1. Restricted uses (Community Management / Marketing APIs)
- Use member data **only to manage the Pages or profiles of the people using your app**. Not for advertising, sales prospecting, recruiting, lead creation, enriching a CRM or marketing-automation tool, building audience lists, ad targeting, account-based marketing or mass messaging.
- **No exporting or transferring** member data out of your app (including to your customers). Data may only be **displayed in your app**, and only to people associated with that Page or profile.
- **No combining** member data with your own data, other LinkedIn data or third-party data to build, extend or verify profiles, leads or reference tables.
- **No social feeds**: you cannot show a Page's LinkedIn posts on a website or intranet.
- **Data minimisation**: request only what the app needs.
- **No fake or headless accounts**; do not manage several customers' accounts from one individual profile.
- Test profiles: up to five, created by hand (not by script), must not interact with real members or Pages (no commenting on real posts, no connecting to real people), must use your own photo.
- Access is for **registered legal organizations with commercial use cases**; a business email address is verified; the app must be verified by a super admin of the organization's Page and must not use LinkedIn or Microsoft names or logos.

## 2. How long data may be stored (Marketing API Program)
| Data | Allowed storage |
|---|---|
| Authenticated member's person id/URN and basic profile | no limit |
| Other members' person id/URN | no limit |
| Other members' basic profile data (e.g. a commenter) | **24 hours** cache only; do not store |
| IDs and URNs for organizations, posts, social actions, ad accounts etc. | no limit |
| Members' social activity (posts, shares, likes, comments, mentions and their metadata) | **48 hours** |
| Organizations' social activity | six weeks; six months if the organization authenticated into your app |
| Organization profile data | eight weeks if the organization authenticated; otherwise not allowed (name and logo URL 30 days) |
| Organization Pages' admin and reporting data (followers, summary of social actions, visitors; no member-level data) | **one year** |
| Advertising account admin and reporting data | one year |
| Lead gen responses | no limit |
| Standardized data lists (industries, functions...) | one year (Bing Maps location data never) |
Where two rules apply the stricter one wins. Members must consent to storing their profile data and can ask for deletion. Not covered by these limits: data your own users type or upload themselves.
**Grey area to ask LinkedIn about:** a member's own *post analytics numbers* (impressions, reactions of their own posts) are not listed by name. Page reporting data is one year; "members' social activity" is 48 hours. If you keep a history of someone's own post numbers longer than 48 hours, ask Developer Support (https://www.linkedin.com/help/linkedin/ask/dsapi) and keep the answer.

## 3. Developer AI Policy (applies to data got through the Marketing/Community Management APIs)
**Design principles** (must/should): accountability and a review body; fairness (no discrimination); **transparency** - tell users they are interacting with AI and that output is AI-generated, how it works, that output may be inaccurate, how to report harmful output, whether their data trains anything or goes to third parties; **"should" restrict automated posting of AI-generated content to external sites (including LinkedIn), or automated execution of generated code, without end-user involvement - and give the user tools to edit generated content before it is published or attributed to them**; give a feedback channel; reliability and safety; if you use a third party's AI, a written agreement at least as protective.

**LinkedIn data as AI input or training data - generally prohibited**, for posts, comments, reactions, messages, profile data, Page profile data and standardized data obtained through the APIs. Exceptions:
- **A. Content created by (or for) people who use your app and consented**: may be used to train or as prompts for: prioritising content for the user's review; sentiment analysis and categorising; accessibility (speech-to-text, text-to-speech, visual recognition); **modifying** content; **creating** posts, comments or messages. Not other people's content, even if it mentions the user, comments on their post or was reposted by them.
- **B. Content by pages or members who are not users of your app**: input/prompt only (no training), and only for prioritising, sentiment/categorising, and accessibility. **Not** for creating or modifying posts, comments or messages.
- Any AI function outside these lists or unrelated to your approved API use cases is prohibited.
Text a person pastes in by hand is "data independently provided to you", which the policy states it does not cover - but stay careful and transparent.

## 4. Access tiers (Community Management API)
| | Development (default) | Standard |
|---|---|---|
| Calls | 500 per app per day, 100 per member per day, all APIs; **no BATCH_GET** | no restrictions |
| Purpose | build and test; finish within **12 months** | live production |
| Risk | access is **removed for inactivity** if you do not apply for Standard within 12 months | |
| How | apply from the app's Products tab; reviewed for approved use case, verified business email, verified organization, website and domain, app verified by the Page | second form + **screen recording** + test credentials; reviewed for use case, privacy policy, compliance and data-storage rules, and a recording showing each core use case |
A rejected app cannot re-apply: create a new app. Changing app functionality after review may need re-review. Use cases named in the review: Page Management, Brand Engagement, Page Analytics, Executive Management (posting to an executive's profile), Employee Advocacy. The screen recording must show: complete OAuth, posting through your app, how a member's comment on that post is displayed, which personal data fields are shown, and aggregate engagement.
Advertising API: Development = read unlimited accounts, edit up to 5; Standard = unlimited (support ticket, video of campaign management).

## 5. Platform rules that bite
- Rate limit numbers and daily resets: file 02. Webhook rules: file 02.
- You are responsible for compliance with the Terms even after approval; LinkedIn can monitor, suspend or withdraw access.
- Breaking-change policy: file 02 section 10.
- Closed permissions (`r_member_social`, `r_full_profile`, compliance scopes) cannot be requested.
- Developer support and news: https://www.linkedin.com/help/linkedin/ask/dsapi, https://www.linkedin.com/content/developers/news, status https://linkedin.statuspage.io/.

## 6. A safe design for a posting-automation tool (derived from the above)
1. A person reviews and approves every post before it is published (the AI policy's "involvement" point), and can edit it first.
2. Label AI help to your users; keep a way to report bad output.
3. Use only your own user's content as AI input; never feed other people's LinkedIn content retrieved through the API into AI.
4. Do not export or combine member data; show it only to the owner of the account.
5. Keep storage within the table above; delete on request.
6. Never scrape LinkedIn or automate the website; use the official API only.
7. Count API calls and stop before the daily limit.
8. Keep secrets out of repositories, chat and logs.
