# 07 - Map of the other LinkedIn API programs

Use this to answer "does LinkedIn have an API for X, and can I get it?". Each program lists its landing page (all under `https://learn.microsoft.com/en-us/linkedin/`). Page-by-page list: `09-page-index.md`.

| Program | What it does | Access | Landing page |
|---|---|---|---|
| **Community Management** | Pages and member profiles: posts, comments, reactions, analytics, notifications, boosts | Vetted; Development then Standard tier (files 01, 03, 04, 06) | `marketing/community-management/community-management-overview` |
| **Advertising (Campaign Management)** | Ad accounts, campaign groups, campaigns, creatives, all ad formats (image, video, carousel, document, article, message, conversation, event, follower, jobs, spotlight, text, VAST), targeting, audience counts/forecasts, budget pricing | Vetted; Development tier edits up to 5 ad accounts (read unlimited); Standard unlimited. 3-legged OAuth only | `marketing/integrations/ads/ads-overview` |
| **Ads Reporting** | `adAnalytics` metrics and pivots, conversion tracking, UTM tracking (dynamic and legacy static), third-party tracking, ad budget pricing | Part of Advertising (`r_ads_reporting`) | `marketing/integrations/ads-reporting/ads-reporting` |
| **Lead Sync** | Pull leads from Lead Gen Forms (ads and events), map custom fields, webhooks | Vetted (Standard tier prerequisite); `r_marketing_leadgen_automation` | `marketing/lead-sync/leadsync-overview` |
| **Conversions API** | Send server-side conversion events (online/offline) for attribution and optimisation; deduplication with the Insight Tag; first-party click ids; payload builder | Apply from the Products tab; `rw_conversions` | `marketing/conversions/conversions-overview` |
| **Matched Audiences** | DMP segments (users, companies, CSV list uploads, destinations), ad segments, website retargeting, predictive audiences | Generally available to qualified developers from Aug 2026; needs Advertising API | `marketing/matched-audiences/matched-audiences` |
| **Event Management** | Create and manage LinkedIn Events, registration forms, event ads | Self-serve on request; some features need Advertising API | `marketing/event-management/event-management-overview` |
| **Audience Insights** | Discover and analyse audiences (demographics, titles, skills, locations) | Private; needs Advertising API; application survey | `marketing/integrations/ads/advertising-targeting/audience-insights-overview` |
| **Media Planning** | Forecast reach/impressions against budget | Private; needs Advertising API; Developer Support request | `marketing/media-planning/media-planning-overview` |
| **Company Intelligence** | Company-level engagement and conversion metrics for target accounts | Private, **not accepting new applications**; use Ad Analytics instead | `marketing/account-intel/company-intelligence-overview` |
| **Experimentation** | A/B testing management, brand lift tests (surveys, benchmarks, results) | Within Advertising | `marketing/integrations/experimentation/overview` |
| **Boost** | Boost organic member/Page posts into ads from your own app | Community Management scopes `*_boost`; new in 202610 | `marketing/community-management/boost/boost-overview` |
| **Sign in / Share / Plugins** | OIDC sign in, share as a member, website plugins | Open (file 05) | `consumer` |
| **Verified on LinkedIn** | Identity/workplace verification signals | Tiered (Development, Lite, Plus) | `consumer/integrations/verified-on-linkedin/overview` |
| **Live Events** | Stream and manage LinkedIn Live (RTMP) | Beta, apply to broadcast | `consumer/integrations/live-video` |
| **Scores, Reviews, 3P Signals** | Write credibility signals to member profiles | Closed beta, invite only | `consumer/integrations/scores-reviews-3p-signals/overview` |
| **LinkedIn Learning** | Learning catalog metadata, activity reports, xAPI webhooks; LMS/HCM deep integrations (Workday, SuccessFactors, Moodle, etc.), SSO (Okta, Azure AD, ADFS, Google, LTI 1.3), SCIM and org-sync user provisioning | Learning Partner Program or an organisation with a Learning site licence; **two-legged OAuth** keys provisioned in Learning Admin Settings | `learning/overview` |
| **Sales Navigator (SNAP)** | Display services (embed iframe), sync services (CRM data validation, profile associations), analytics services (user activity exports) | **Not accepting new partners** | `sales` |
| **Talent Solutions** | Recruiter System Connect, Apply Connect, Apply with LinkedIn, Job Posting API and XML feeds, CRM Connect, middleware platform (sync jobs, candidates, applications), push events | Partner applications (ATS partners); `talent` | `talent` |
| **Compliance** | Archive and monitor member activity for regulated industries: Compliance Events, Snapshot, Management, Sales Navigator compliance, groups, request limits | **Closed** (no new requests); needs agreement + `r_compliance` | `compliance-api/overview` |
| **DMA data portability** (Pages data portability) | EU Digital Markets Act: members' and Pages' data (activities, organizations, people, live videos, lead gen forms, geo, industry) | Scopes such as `r_dma_admin_pages_content` | `dma/pages-data-portability/...` (see page index) |

## Three things people trip over
1. **Marketing = 3-legged OAuth only.** Client credentials work only for programs where LinkedIn enabled them (e.g. Learning, some enterprise cases).
2. **Several programs are closed to new partners** (Sales Navigator, Company Intelligence, Compliance, Scores/Reviews). Do not plan a product on them.
3. **Member data restrictions follow you into every marketing program**: see file 06.
