# 02 - How requests work (Rest.li, headers, versions, errors, limits, webhooks)

Sources: shared/api-guide/concepts/* (data-formats, methods, protocol-version, projections, pagination, decoration, query-tunneling, error-handling, rate-limits, urns), shared/api-guide/webhook-validation, shared/development-resources/api-clients, marketing/versioning, marketing/error-responses, shared/breaking-change-policy.

## 1. Base URLs and headers
| Thing | Value |
|---|---|
| OAuth authorize / token host | `https://www.linkedin.com/oauth/v2/...` (NOT api.linkedin.com) |
| Versioned APIs (marketing, posts, analytics, images...) | `https://api.linkedin.com/rest/<resource>` |
| Older "v2" APIs (profile, userinfo, socialActions, ugcPosts, assets) | `https://api.linkedin.com/v2/<resource>` |
| Auth header | `Authorization: Bearer <access token>` |
| Protocol | `X-Restli-Protocol-Version: 2.0.0` (without it the call is treated as protocol 1.0) |
| Version (rest only) | `Linkedin-Version: 202610` (YYYYMM). The docs also spell it `X-LinkedIn-Version`; both appear in LinkedIn material, use `Linkedin-Version` as in all the samples |
| Body | JSON only (`Content-Type: application/json`); XML is not supported in or out |
| TLS | TLS 1.0 is not supported; always HTTPS |

Each versioned call must name its version. LinkedIn does **not** default to the latest. A missing header and a retired version both return an error (retired = `426`).

## 2. Versioning
- Monthly releases from June 2022 under `/rest/`; each version is supported **at least 12 months** then sunset. Migrating = change the header value, then re-test, because behaviour and fields can change between versions.
- Latest: `202610`. See `10-versions-and-changes.md` for the table and sunset dates.
- Each documentation page has a version picker; the pages carry `monikers` like `li-lms-2026-10`. The default view is the latest.
- Individual resources evolve at different times; check the page's "Recent changes"/migration notes.

## 3. Rest.li 2.0 encoding (the thing that breaks most hand-written clients)
- **Resource keys**: URL-encode the *whole* key. `( ) : ,` become `%28 %29 %3A %2C`. e.g. `/rest/posts/urn%3Ali%3Ashare%3A123`.
- **Parameters** that are not resource keys keep their structural characters: `entity=(share:urn%3Ali%3Ashare%3A123)`, `dateRange=(start:(day:4,month:5,year:2024),end:(day:6,month:5,year:2024))`, `ids=List(urn%3Ali%3Ashare%3A1,urn%3Ali%3Ashare%3A2)`. Encode the *values* inside, not the commas/parentheses that group them.
- **Never let an HTTP library encode a value twice.** Build the query string yourself when it contains pre-encoded URNs (a `params` dict encodes `%3A` again; LinkedIn answers 400).
- Compound key: `(stringKey:abc,longKey:5)`. Lists: `List(a,b,c)`.
- Protocol 1.0 is slated for deprecation; do not use it in new code.
- Official client libraries (JavaScript, Python; GitHub `linkedin-developers/linkedin-api-js-client` and `linkedin-api-python-client`) do the encoding, versions, tunneling and all Rest.li methods for you. They do not know specific APIs, only the protocol.

## 4. Methods
| Method | HTTP | Notes |
|---|---|---|
| GET | GET `/{service}/{key}` | one entity |
| GET_ALL | GET `/{service}` | all entities |
| BATCH_GET | GET `?ids=List(...)` plus header `X-RestLi-Method: BATCH_GET` | several by key. **Not allowed on the Community Management Development tier** |
| FINDER | GET `?q={finderName}&...` | search by criteria; may return 0..n |
| BATCH_FINDER | GET `?bq={name}` | several filter sets in one call |
| CREATE | POST body | 201, new id in the `x-restli-id` response header |
| BATCH_CREATE | POST | |
| UPDATE | PUT | full overwrite |
| PARTIAL_UPDATE | POST plus header `X-RestLi-Method: PARTIAL_UPDATE`, body `{"patch":{"$set":{...}}}` | edit some fields (this is how a post is edited) |
| BATCH_PARTIAL_UPDATE | POST plus `X-RestLi-Method: BATCH_PARTIAL_UPDATE` | |
| DELETE / BATCH_DELETE | DELETE | idempotent: deleting twice returns 204 |
| ACTION | POST `?action={name}` | e.g. `initializeUpload`, `finalizeUpload`, and on `/v2/developerApplicationsSecurity` the actions `rollDeveloperApplicationSecret` and `removeDeveloperApplicationSecret` |

Success codes seen: 200 read, 201 created, 202 accepted (async), 204 no content (update/delete).

## 5. Projections, decoration, pagination, URNs
- **Projection**: `fields=id,baz:(beep)` limits response fields (v2: `projection=(...)`). Child objects `parent:(a,b)`; maps `baz:($*:(beep))`.
- **Decoration**: fetch the object a URN points to in the same call by adding `~` to the field name in the projection, e.g. `projection=(id,owner~(localizedFirstName))` returns `owner~`. Deprecated in some marketing API versions; see recent changes.
- **Pagination**: `start` (default 0) and `count` (default 10). A page with fewer than `count` elements is the last. Some finders cap `count` (posts finder max 100; images/videos list 1,000). Search APIs under Ads use cursor-based pagination: `pageSize` (default 100) and `pageToken`, taking `nextPageToken` from the response metadata.
- **URNs**: `urn:{namespace}:{type}:{id}`, max 255 chars, e.g. `urn:li:person:xxx`, `urn:li:organization:123`, `urn:li:share:123`, `urn:li:ugcPost:123`, `urn:li:activity:123`, `urn:li:comment:(urn:li:activity:123,456)`, `urn:li:image:C4...`, `urn:li:video:C5...`, `urn:li:document:D...`. A bare id is the key without the prefix. Always URL-encode a URN used inside a URL.
- **Query tunneling**: a request over limits gets `414`. Limits: raw URL 8 KB, query string 4 KB, request URL incl. headers 28 KB, path segment 4 KB. Fix: send POST with `X-HTTP-Method-Override: GET` (or POST/PUT), `Content-Type: application/x-www-form-urlencoded`, and move the query string into the body (with a body use `multipart/mixed; boundary=...`).
- The official client libraries tunnel automatically.

## 6. Errors
Standard shape: `{"message": "...", "serviceErrorCode": 100, "status": 403}`. Newer marketing resources (ad accounts, campaign groups, campaigns) add `code`, `errorDetailType` (`com.linkedin.common.error.BadRequest`) and `errorDetails` with `inputErrors` / `conditionalInputErrors` (each with `code`, `input.inputPath.fieldPath`, `description`, min/max info). If `code` is present you have the new format; also some old 400s for "viewer may not have permission" became 403.

| Status | Meaning and usual fix |
|---|---|
| 400 | Bad syntax: invalid characters in URL, wrong or double-encoded URN, bad field. Also "Unsupported query type ... for metric type ..." for a bad analytics combination |
| 401 | Missing/invalid/expired/revoked token or wrong header format. "Access token downstream verification failures return 500" |
| 403 | Token lacks the permission, member has no role on that Page/ad account, product not on app, or a restricted API |
| 404 | Wrong path or entity missing. For Ads, can also mean a restricted API. Posts: `Unable to obtain corresponding activityUrn` = post not found in that API |
| 405 | Method not supported by that resource |
| 409 | Write conflict (posts) - retry |
| 411 | POST with empty body needs `Content-Length: 0` |
| 414 | URL too long - use query tunneling |
| 422 | Valid syntax, semantic problem |
| 426 | `Linkedin-Version` retired or unsupported - move to a supported version |
| 429 | Rate limit (`Resource level throttle limit for calls to this resource is reached`), or comment creation throttle (`Comment create throttled: creation rate limit exceeded for member` = short 1-minute limit), or rare infrastructure protection. Back off and retry later |
| 500 / 503 / 504 | LinkedIn side. Retry with backoff; if it persists record `x-li-uuid`, `x-li-fabric`, `x-li-request-id`, URL, method and client id for support |

Rule from the breaking-change policy: **branch on status and code, not on message text.**

## 7. Rate limits
- Limits are per **24 hours, reset at midnight UTC** (05:30 IST).
- Two kinds: **application** (all calls by the app) and **member** (calls made with one member's token for the app).
- Numbers are not published in the docs; read them in the Developer Portal: app, **Analytics** tab, "Usage & Limits" / 24-hour quotas (shows only endpoints called at least once today UTC; make a test call to make one appear).
- Developer Admins get an email at **75%** of an *application* limit (not for member-level limits), delayed 1-2 hours.
- Known limits: Community Management Development tier 500/app and 100/member per day for all APIs (raised from 100/10 in 2025); BATCH_GET not allowed on that tier. Share on LinkedIn legacy: 150/member and 100,000/app per day.
- 429 means too many redundant calls: cache, refresh less often, check the portal's usage table.

## 8. Webhooks
Only for apps with an approved webhook use case (e.g. organization social action notifications, Lead Sync, Apply Connect, Learning xAPI).
1. Register the URL in the app's **Webhooks** tab (Lead Sync subscriptions are created by API instead). HTTPS only; ngrok URLs are rejected.
2. **Validation**: LinkedIn sends `GET <url>?challengeCode=<uuid>`; reply 200 JSON `{"challengeCode": "...", "challengeResponse": "<hex HMAC-SHA256 of the challengeCode using the app client secret as key>"}`. Failure message: `This URL did not pass the security challenge check`. Re-validated every **2 hours**; three failures in a row = blocked, events stop, emails sent; revalidate manually in the portal after fixing.
3. **Every event**: LinkedIn POSTs JSON with header `X-LI-Signature` = hex HMAC-SHA256 of the string `"hmacsha256=" + <raw body>` using the client secret. Compare in constant time over the raw body exactly as received (no re-serializing). Reject mismatches.
4. Return any **2xx** quickly; anything else counts as failure. Deduplicate by notification id. Redelivery for organization notifications: every 5 minutes for 8 hours.
5. Subscriptions for a member die when that member's grant is revoked or expires, or they stop being Page admin.

## 9. Good practice list (from the best-practices pages)
- Cache tokens; one consent for all scopes; show the signed-in member; allow logout and destroy tokens.
- Handle every failure: assume any call can fail; log the support ids above.
- Do not store secrets in client-side code, logs or error messages; HTTPS everywhere; use `state` against CSRF; vet third-party libraries (LinkedIn does not support them).
- Ask for the minimum scopes and member data.
- Watch the changelog and email notices; use the Developer Portal Endpoint Catalog and App Insights; status page https://linkedin.statuspage.io/.

## 10. What counts as breaking (breaking-change policy)
Breaking: changed permissions, removed parameter or field, new required field without default, changed endpoint behaviour, new validation. Non-breaking and can arrive unannounced: new endpoints/methods/fields/enum values, reordered fields, new optional headers, changed error messages, size changes. Write clients that ignore unknown fields and tolerate new enum values. LinkedIn may break things without notice for security, privacy or legal reasons.
