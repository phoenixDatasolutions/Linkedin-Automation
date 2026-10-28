# 04 - Analytics: your numbers from the API

Sources (under `https://learn.microsoft.com/en-us/linkedin/marketing/community-management/`): `members/post-statistics`, `members/follower-statistics`, `members/video-statistics`, `organizations/share-statistics`, `organizations/page-statistics`, `organizations/follower-statistics`, `organizations/organization-lookup-api` (networkSizes), `organizations/organization-social-action-notifications`, `shares/video-analytics-api`, `boost/boost-analytics`.

All numbers are "best effort" and must not be used for billing. Limits: Community Management Development tier allows 100 calls per member and 500 per app per day.

## 1. Member (personal profile) analytics - permission `r_member_postAnalytics`
Endpoint: `GET /rest/memberCreatorPostAnalytics`. **One post and one metric per call. No batching.**

| Finder | Question it answers | Call |
|---|---|---|
| `entity` | One post, one metric | `?q=entity&entity=(share:urn%3Ali%3Ashare%3A123)&queryType=IMPRESSION&aggregation=TOTAL` (use `ugc:urn%3Ali%3AugcPost%3A123` for ugcPost URNs) |
| `me` | One metric summed across ALL your posts | `?q=me&queryType=IMPRESSION&aggregation=TOTAL` |

Parameters: `queryType` (required), `aggregation` = `TOTAL` (default, one data point) or `DAILY` (one point per day), `dateRange=(start:(day:4,month:5,year:2024),end:(day:6,month:5,year:2024))` (start inclusive, end exclusive; omitted = lifetime).

Metrics (`queryType`):
| Metric | Meaning | Versions |
|---|---|---|
| IMPRESSION | times the post was shown | all |
| MEMBERS_REACHED | unique viewers | all (no DAILY) |
| REACTION | reactions | all |
| COMMENT | comments | all |
| RESHARE | reposts | all |
| POST_SAVE | saves | 202604+ |
| POST_SEND | sent via messaging | 202604+ |
| LINK_CLICKS | clicks on links in the post | 202604+ (no DAILY) |
| PREMIUM_CTA_CLICKS | premium call-to-action clicks | 202604+ |
| FOLLOWER_GAINED_FROM_CONTENT | followers gained | 202604+ (no DAILY) |
| PROFILE_VIEW_FROM_CONTENT | profile views driven | 202604+ (no DAILY) |

Response: `{"elements": [{"count": 10, "metricType": "REACTION", "targetEntity": {"share": "urn:li:share:..."}, "dateRange": {...}}], "paging": {...}}`. Up to version 202604 `metricType` was wrapped in a namespaced object; from 202605 it is a plain string - parse both.
Known notes from the docs: daily IMPRESSION is not supported when the entity is a post; for the `me` finder RESHARE/REACTION/COMMENT "are not consistent with the LinkedIn UI at the moment". Errors: 400 for unsupported aggregation/metric combinations, 500 intermittent (retry).

Cost planning: views + comments + reposts for one post = 3 calls. Ten posts = 30 calls. Refresh new posts often and old posts rarely (their numbers barely move). Cache answers.

Related member endpoints:
- `GET /rest/memberFollowersCount?q=me` lifetime follower count; `q=dateRange&dateRange=(...)` daily followers. Permission `r_member_profileAnalytics` (restricted to members).
- `GET /rest/memberCreatorVideoAnalytics?q=entity&entity=(...)&queryType=VIDEO_PLAY|VIDEO_VIEWER|VIDEO_WATCH_TIME` (watch time in ms; only for video posts; VIDEO_PLAY/VIEWER data unavailable after one year; VIEWER and WATCH_TIME have no DAILY). Permission `r_member_postAnalytics`.

## 2. Company Page analytics - permission `rw_organization_admin` (ADMINISTRATOR role)
- **Share statistics** `GET /rest/organizationalEntityShareStatistics?q=organizationalEntity&organizationalEntity={enc org urn}`; add `shares=List(urn%3Ali%3Ashare%3A1,...)` or `ugcPosts=List(...)` to get **several posts in one call** (lifetime only), or `timeIntervals=(timeGranularityType:DAY|MONTH,timeRange:(start:ms,end:ms))` for time series. Organic only (ads are in Ad Analytics). Rolling **12-month** window. Fields: `impressionCount`, `uniqueImpressionsCount`, `clickCount`, `likeCount`, `commentCount`, `shareCount`, `engagement`. No pagination. Posts with no activity are omitted: treat missing as zero. Like counts can go negative for sponsored shares. `socialActions`/`socialMetadata` give live like/comment counts that match the feed.
- **Page statistics** `organizationPageStatistics` (and `brandPageStatistics`): lifetime or time-bound page views and clicks, segmented by facets (mobile/desktop/overall); careers page views only for pages that pay for career pages.
- **Follower statistics** `organizationalEntityFollowerStatistics`: lifetime counts by 7 facets (association type, geo country, geo, function, industry, seniority, staff count range), top 100 each; time-bound (`timeIntervals` with granularity DAY/WEEK/MONTH) returns totals only, no facets, from 12 months ago until 2 days ago. Total follower count: `GET /rest/networkSizes/{enc org urn}?edgeType=COMPANY_FOLLOWED_BY_MEMBER` (older versions up to 202304 used `CompanyFollowedByMember`).
- **Video analytics** `videoAnalytics`: watch time, video views, viewers for a video entity.
- **Boost analytics** `/boostAnalytics` (202610+): needs `r_member_boost`/`rw_member_boost` (member posts) or `r_organization_boost`/`rw_organization_boost` (Page posts).

## 3. Notifications instead of polling
Webhooks for page activity (`ORGANIZATION_SOCIAL_ACTION_NOTIFICATIONS`): actions LIKE, COMMENT, SHARE, SHARE_MENTION, ADMIN_COMMENT, COMMENT_EDIT, COMMENT_DELETE; only for PUBLIC posts; needs a validated webhook, each member authorising `rw_organization_admin`, and a subscription per member + organization. Batches of 10, redelivery every 5 minutes for 8 hours, dedupe on `notificationId`. Pull API `organizationalEntityNotifications?q=criteria` keeps 60 days. See `02-api-mechanics.md` section 8 for webhook security. Webhooks need an approved use case.

## 4. Storage and use of what you fetch
Page admin and reporting data (no member-level detail) may be stored one year; members' social activity 48 hours. Details and caveats: `06-rules-and-policies.md`.
