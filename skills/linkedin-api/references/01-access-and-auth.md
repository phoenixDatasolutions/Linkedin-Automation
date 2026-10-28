# 01 - Access, products, permissions and authentication

Sources: shared/authentication/* (authentication, getting-access, authorization-code-flow, client-credentials-flow, programmatic-refresh-tokens, developer-portal-tools, token-introspection, application-secret-management), marketing/increasing-access, marketing/quick-start, marketing/getting-started, marketing/community-management-app-review. All under `https://learn.microsoft.com/en-us/linkedin/`.

## 1. How a developer gets API access
1. Create a LinkedIn **Page** for the organization (real legal entity for Community Management).
2. Create a **developer app** at https://www.linkedin.com/developers/apps/new and have a super admin of the Page **verify** the app (associate app with Page).
3. Open the app's **Products** tab and add or apply for a product. Open products are instant; vetted ones need review.
4. The **Auth** tab shows which scopes the app can ask for; client ID and secret live there. Add the HTTPS redirect URLs there (absolute, no `#`, query strings ignored).
5. Test with the Developer Portal **Token Generator** (https://www.linkedin.com/developers/tools/oauth/token-generator) or Postman.

### Open products (any developer, self-service)
| Product | Scopes | Use |
|---|---|---|
| Sign in with LinkedIn using OpenID Connect | `openid`, `profile`, `email` | Authenticate a member and read name, photo, email |
| Share on LinkedIn | `w_member_social` | Post, comment and react as the member (UGC/Posts API) |

If a scope is not provisioned on the app, the authorize page fails with `unauthorized_scope_error` ("Scope ... is not authorized for your application"). Fix = add the product, do not just add the scope.

### Vetted / partner products (apply; review by LinkedIn)
| Product | Notes |
|---|---|
| Community Management API | Development tier then Standard tier. Registered legal organizations, commercial use only. Must be the only product on its app. |
| Advertising API | Development: read unlimited ad accounts, edit up to 5. Standard: unlimited. |
| Lead Sync, Conversions, Events Management | Self-serve on request from the Products tab. |
| Matched Audiences | Generally available from August 2026 to qualified developers (requires Advertising API). |
| Audience Insights, Media Planning | Private; need Advertising API plus an application survey. |
| Company Intelligence | Private; not accepting new applications. |
| Learning, Sales Navigator (SNAP), Talent (RSC, Apply Connect, Apply with LinkedIn, Job Posting), Compliance | Partner programs; Compliance is **closed** to new requests. |

### Closed permissions (cannot be requested)
`r_member_social` (read posts/comments/likes of members), `r_full_profile`, `r_compliance`, `w_compliance`. Plan around them; they are not "pending approval".

## 2. Permissions (scopes) used by marketing and community APIs
All are member (3-legged) permissions. A member must accept **all** scopes in one go; request the fewest possible.

| Scope | What it allows |
|---|---|
| `w_member_social` | Create posts, comments, reactions as the member |
| `w_member_social_feed` | Create/modify/delete comments and reactions as the member |
| `r_member_social` / `r_member_social_feed` | Read member posts/comments/reactions. **Closed / select developers only** |
| `r_member_postAnalytics` | Member post analytics and member video analytics (`memberCreatorPostAnalytics`, `memberCreatorVideoAnalytics`) |
| `r_member_profileAnalytics` | Member profile analytics: followers (`memberFollowersCount`), profile viewers, search appearances. Restricted to members |
| `w_organization_social` | Post/comment/react as an organization. Needs role ADMINISTRATOR, DIRECT_SPONSORED_CONTENT_POSTER or CONTENT_ADMINISTRATOR |
| `r_organization_social` | Read the organization's posts, comments, likes |
| `w_organization_social_feed` / `r_organization_social_feed` | Comments/reactions/social metadata as or for an organization |
| `r_organization_admin` | Read the organization's pages and reporting (follower, visitor, content analytics) |
| `rw_organization_admin` | Manage pages and retrieve reporting; ADMINISTRATOR only. Needed for follower, page and share statistics and for notification subscriptions |
| `r_organization_followers` | Follower data (used to mention followers) |
| `r_member_boost`, `rw_member_boost`, `r_organization_boost`, `rw_organization_boost` | Boost API (new in 202610) |
| `r_basicprofile`, `r_1st_connections_size` | Basic profile; number of 1st-degree connections |
| `r_ads`, `rw_ads`, `r_ads_reporting` | Advertising |
| `r_marketing_leadgen_automation` | Lead Sync |
| `rw_conversions` | Conversions API |
| `rw_dmp_segments` | Matched Audiences |
| `r_events`, `rw_events` | Events Management |
| `r_sales_nav_analytics`, `r_sales_nav_display` (member), `r_sales_nav_validation`, `r_sales_nav_profiles` (application) | Sales Navigator |

Retired names that still turn up in old code: `r_liteprofile`, `r_emailaddress` (replaced by OpenID `profile`/`email`), `r_ads_leadgen_automation` (July 2023), `rw_offlineConversions` (Oct 2023).

Changing the scope list of an app means every user must re-authorize. **Requesting a different scope than before invalidates the earlier access tokens** for that member.

### Company Page roles
ADMINISTRATOR, DIRECT_SPONSORED_CONTENT_POSTER, RECRUITING_POSTER, LEAD_CAPTURE_ADMINISTRATOR, LEAD_GEN_FORMS_MANAGER, ANALYST (analytics tab only), CURATOR, CONTENT_ADMINISTRATOR. Role state: APPROVED, REJECTED, REQUESTED, REVOKED. Page roles can only be granted in the LinkedIn UI, not via the API. Check roles with `GET /rest/organizationAcls?q=roleAssignee` (member's pages) or `q=organization` (a page's admins). A frequent error cause: calling a Page endpoint with a token of a member who has no role on that Page.

Ad account roles: VIEWER, CREATIVE_MANAGER, CAMPAIGN_MANAGER, ACCOUNT_MANAGER, ACCOUNT_BILLING_ADMIN (only one per account).

## 3. Authorization Code flow (3-legged OAuth)
1. Send the browser to `GET https://www.linkedin.com/oauth/v2/authorization` with `response_type=code`, `client_id`, `redirect_uri` (must exactly match a registered URL), `scope` (space separated, URL encoded), and a hard-to-guess `state` (check it on return; mismatch = reject, likely CSRF). Add `enable_extended_login=true` for native apps to allow Google/Apple/passkey login.
2. The member consents; LinkedIn redirects to `redirect_uri?code=...&state=...`. The **code lives 30 minutes** and is single use. A cancel returns `error=user_cancelled_login` or `user_cancelled_authorize` plus `error_description`.
3. Exchange it: `POST https://www.linkedin.com/oauth/v2/accessToken` (note host `www.linkedin.com`, not `api`), `Content-Type: application/x-www-form-urlencoded`, body `grant_type=authorization_code`, `code`, `client_id`, `client_secret`, `redirect_uri`. Secret goes in the **body**, never in the URL.
4. Response: `access_token` (about 500 chars; plan for 1,000+), `expires_in` (5,184,000 s = 60 days), `scope`, and for approved apps `refresh_token` and `refresh_token_expires_in`.
5. Call APIs with `Authorization: Bearer <token>`.
6. Common 400/401s: `Redirect_uri doesn't match`, `Client_id doesn't match`, `Invalid scope`, "authorization code not found / expired", or `invalid_redirect_uri` ("appid/redirect uri/code verifier does not match authorization code. Or authorization code expired. Or external member binding exists").

Tokens: you may hold several valid tokens for the same scope set. Cache the token; do not log in per call; destroy tokens on logout. LinkedIn may revoke tokens at any time; on 401 fall back to the normal consent flow.

## 4. Refresh tokens
Only approved Marketing Developer Platform partners get programmatic refresh tokens. Access token TTL 60 days; refresh token TTL 365 days and **does not extend** when used (day 59 refresh: new access token 60 days, refresh token has 306 left). Exchange: `POST /oauth/v2/accessToken` with `grant_type=refresh_token`, `refresh_token`, `client_id`, `client_secret`. If refresh fails (expired, revoked) the member must re-authorize. Everyone else renews by sending the member through authorization again (the screen is skipped when they are still signed in to linkedin.com and the old token has not expired). The Developer Portal analytics page has a refresh-token usage quota table.

## 5. Client credentials flow (2-legged)
For APIs that are not member-specific and only for apps LinkedIn has enabled (not available for Marketing APIs). `POST /oauth/v2/accessToken` with `grant_type=client_credentials`, `client_id`, `client_secret` (URL-encode secrets: they can contain `/`, `=`, `+`). Token lasts **30 minutes**. `access_denied: This application is not allowed to create application tokens` = the app was never enabled for 2L.

## 6. Token tools
- **Token Generator** and **Token Inspector** in the Developer Portal; the inspector also builds a ready cURL.
- **Token introspection API**: POST `https://www.linkedin.com/oauth/v2/introspectToken` with form `client_id`, `client_secret`, `token`. Returns `active`, `status` (active/expired/revoked), `scope` (3-legged only), `created_at`, `expires_at`, `authorized_at`, `auth_type` (`3L`, `2L`, `Enterprise_User`). 400 bad client id or token; 401 bad secret; credentials valid but token from another app = 200 with `active:false`.

## 7. Application secrets
Each app can hold **two client secrets** at once. Rotate: Auth tab, "Generate a New Client Secret" - the old one becomes the secondary and keeps working - update configs, test, then remove the secondary. Recommended rotation every 60-90 days and after any exposure. A rotate API exists: `POST https://api.linkedin.com/v2/developerApplicationsSecurity?action=rollDeveloperApplicationSecret` (and `action=removeDeveloperApplicationSecret`), with `X-RestLi-Method: action`, `X-RestLi-Protocol-Version: 2.0.0` and a 2L/3L bearer token made from the app's credentials; the body is `{}`. Never pass the secret in a URL, log, chat or client-side file. If an app already has two secrets, delete one before rotating.

## 8. Quick checklist when sign-in breaks
- Product added on the app? (scope must be provisioned) 
- Redirect URI identical, including trailing slash and scheme?
- Code reused or older than 30 minutes?
- `state` mismatch (cookie lost, second browser)?
- Client secret was rotated/overwritten and the stored copy is stale?
- Wrong app's credentials in the wrong slot?
- Token expired (60 days) or the member removed the app in LinkedIn settings (revoked)?
