# 10 - Versions, recent changes, migrations

Sources: `marketing/versioning`, `marketing/integrations/recent-changes`, `marketing/integrations/migrations`, `marketing/community-management/contentapi-migration-guide`, `marketing/community-management/community-management-api-migration-guide`, `marketing/error-responses`, `shared/breaking-change-policy`. Snapshot taken 2026-10-29.

## Version rules
- Header `Linkedin-Version: YYYYMM`, required on every `/rest/` call; never defaulted. Monthly releases; each version supported **at least 12 months**, then removed. Missing header or a retired version returns an error (`426` for retired).
- To migrate: change the header value, read the changelog for each resource you use, re-test. You may skip versions.
- Latest: **202610**.

## Sunset schedule (from the migration status table)
| Version | Sunset | Status on 2026-10-29 |
|---|---|---|
| 202510 | 2026-10-15 | already sunset (deprecated) |
| 202511 | 2026-11-16 | deprecated, ending soon |
| 202601 | 2027-01-15 | active |
| 202602 | 2027-02-15 | active |
| 202603 | 2027-03-16 | active |
| 202604 | 2027-04-15 | active |
| 202605 | 2027-05-15 | active |
| 202606 | 2027-06-15 | active |
| 202607 | 2027-07-15 | active |
| 202608 | 2027-08-17 | active |
| 202609 | 2027-09-15 | active |
| 202610 | 2027-10-15 | active (latest) |
Pattern: sunset is about 12 months after release, around the 15th.

## Recent changes worth knowing (Marketing / Community Management)
- **202610**: Boost API for member and Page posts (Boost Init, Hydrate, Post, Status, Analytics; scopes `r_/rw_member_boost`, `r_/rw_organization_boost`); Creatives `metadata`; Company Intelligence `jobFunction` filter; Ads reporting `memberFollows`, `memberProfileClicks`.
- **202611 (coming)**: publisher lists require a `surface` field (`LAN` or `CTV`) or return 400.
- **202609**: Company Intelligence filters; Ads reporting pivot `MEMBER_DESIGNATED_MARKET_AREA`; Conversions hashed names; 180-day attribution option.
- **202608**: Matched Audiences API generally available; DMP segment cap 1,000 per account (429 `SEGMENT_LIMIT_EXCEEDED`); Dynamic UTM at account level. Legacy Geo targeting stopped 2026-08-31 (use Bing Geo); `location` removed from `/v2/me` and `/v2/people` (use `geoLocation`).
- **202604+**: member post analytics gained POST_SAVE, POST_SEND, LINK_CLICKS, PREMIUM_CTA_CLICKS, FOLLOWER_GAINED_FROM_CONTENT, PROFILE_VIEW_FROM_CONTENT. From 202605 the analytics `metricType` is a plain string.
- Community Management Development tier limits were raised (app 100 to 500, member 10 to 100 calls per day; the docs give no date).
- 202602: Videos API fields `templateName`, `linkbackContext`. 202307: reaction `MAYBE` removed. 202305: `networkSizes` edge type renamed `COMPANY_FOLLOWED_BY_MEMBER`. 202301: find posts by *person* author supported.

## Legacy -> current API map
| Legacy | Replacement |
|---|---|
| Share API, UGC Posts API (`/v2/shares`, `/v2/ugcPosts`) | Posts API `/rest/posts` |
| Assets API (`registerUpload`, `digitalMediaAsset`) | Images API, Videos API, Documents API (`initializeUpload`, `finalizeUpload`; URN `urn:li:image:`/`video:`/`document:`) |
| Likes in `socialActions` | Reactions API `/rest/reactions` |
| `socialActions` comments (v2) | `/rest/socialActions/{urn}/comments` |
| `socialActions` summary | Social Metadata `/rest/socialMetadata` |
| AdCreativesV2 | Creatives API (id becomes a `urn:li:sponsoredCreative:`) |
| sponsoredConversations / AdInMailContentsV2 | conversationAds / InMailContents |
| Ads Lead Sync and Events Lead Sync | Lead Sync API (sunset 2024-12-16) |
| Offline Conversions | Conversions API |
| Unversioned marketing APIs | versioned `/rest/` APIs (unversioned sunset 2024-12-16) |
| `r_liteprofile`, `r_emailaddress`, `w_share` | OpenID `profile`/`email`, `w_member_social` |
| Protocol 1.0 | Rest.li 2.0.0 |

## Posts migration details
Share API -> Posts: `owner`->`author`, `content.commentary`->`commentary`, `resharedShare`->`reshareContext.parent`, `originalShare`->`reshareContext.root`; article fields move under `content.article` (title, source). UgcPosts -> Posts: `specificContent`->`content`, attributed commentary -> a single `little` string, `targetAudience`->`distribution.targetEntities`, `externalDistributionChannels`->`thirdPartyDistributionChannels`, dark posts = `distribution.feedDistribution NONE` + `visibility PUBLIC`, AuditStamps flattened to `createdAt`/`lastModifiedAt`/`createdBy`/`lastModifiedBy`; thumbnails for article posts must be uploaded by you.

## Habit that avoids pain
Put the version in one constant/env var, review the changelog monthly, and add a "retired version" fallback: on `426`, probe the newest versions until one is accepted and log it loudly.
