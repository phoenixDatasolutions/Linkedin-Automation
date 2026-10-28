# 03 - Posting and engagement (Posts, media, comments, reactions)

Sources (all under `https://learn.microsoft.com/en-us/linkedin/marketing/community-management/`): `shares/posts-api`, `shares/post-api-schema`, `shares/images-api`, `shares/videos-api`, `shares/documents-api`, `shares/multiimage-post-api`, `shares/poll-post-api`, `shares/celebration-post-api`, `shares/little-text-format`, `shares/comments-api`, `shares/reactions-api`, `shares/social-metadata-api`, `shares/posts-atmention-search-api`, `contentapi-migration-guide`, `usecases/page-management/organic-posts-usecase`, and the legacy `shares/network-update-social-actions`, `shares/vector-asset-api`. Legacy member sharing: `consumer/integrations/self-serve/share-on-linkedin` (file 05).

All calls: `Linkedin-Version: YYYYMM` + `X-Restli-Protocol-Version: 2.0.0` + `Authorization: Bearer`, base `https://api.linkedin.com/rest`.

## 1. Which token and permission for which job
| Job | Token of | Scope |
|---|---|---|
| Post as a person | that person | `w_member_social` |
| Post as a Company Page | a member with role ADMINISTRATOR, DIRECT_SPONSORED_CONTENT_POSTER or CONTENT_ADMINISTRATOR on the Page | `w_organization_social` |
| Comment / react as a person | that person | `w_member_social` (docs also list `w_member_social_feed`) |
| Comment / react as a Page | Page admin | `w_organization_social_feed` |
| Read a Page's posts, comments, likes | Page admin | `r_organization_social` (`r_organization_social_feed` for social actions) |
| Read a person's posts/comments/reactions | person | `r_member_social` / `r_member_social_feed` - **closed**, cannot be obtained |
| Upload images/videos/documents | owner of the asset | `w_member_social` or `w_organization_social` (these two are write-only: a token holding only `w_member_social` cannot GET `/rest/images` on the versioned gateway) |

Author URN: person = `urn:li:person:{id}` (id comes from the OpenID `sub` or `GET /v2/me`), page = `urn:li:organization:{id}`.

## 2. Posts API (`/rest/posts`) - replaces ugcPosts and the Share API
Content types: text only, image, video, document, article, multiImage, poll, celebration (celebration cannot be created through the external API); carousel is sponsored only; reshare via `reshareContext`.

### Create (POST `/rest/posts`)
Required: `author`, `commentary` (the text, "little" format), `visibility`, `distribution`, `lifecycleState`.
```json
{
  "author": "urn:li:person:XXXX",
  "commentary": "Text of the post",
  "visibility": "PUBLIC",
  "distribution": {"feedDistribution": "MAIN_FEED", "targetEntities": [], "thirdPartyDistributionChannels": []},
  "lifecycleState": "PUBLISHED",
  "isReshareDisabledByAuthor": false
}
```
- Success = `201`; the new post id is in the **`x-restli-id` response header** (`urn:li:share:...` or `urn:li:ugcPost:...`). The body is empty.
- `visibility`: `PUBLIC`, `CONNECTIONS`, `LOGGED_IN`, `CONTAINER`. `feedDistribution`: `MAIN_FEED` or `NONE` (NONE + PUBLIC = a "dark post" for ads).
- `lifecycleState` on create is `PUBLISHED` only. On read you can also see `DRAFT`, `PUBLISH_REQUESTED` (async processing), `PUBLISH_FAILED` (edit then retry). `lifecycleStateInfo` carries `contentStatus`, `reviewStatus` (PENDING/PROCESSING/FAILED) and `isEditedByAuthor`.
- Targeted organic posts: `distribution.targetEntities` with industries, seniorities, job functions, geoLocations etc.; the audience must exceed **300 members** (check with `audienceCounts`).
- Link to a post in the browser: `https://www.linkedin.com/feed/update/urn:li:ugcPost:<id>/`.
- Max lengths come back as `FIELD_LENGTH_TOO_LONG` (400); commentary is capped (LinkedIn's UI cap is 3,000 characters).

### Content blocks (`content`)
- **Image or video**: `{"media": {"id": "urn:li:image:...", "title": "...", "altText": "..."}}` (video id `urn:li:video:...`; alt text up to 4,086 chars, under 120 recommended).
- **Document**: `{"media": {"title": "<required>", "id": "urn:li:document:..."}}`.
- **Article/link post**: `{"article": {"source": "https://...", "thumbnail": "urn:li:image:...", "title": "...", "description": "..."}}`. The Posts API does **not scrape** the URL: you must supply title, description and an uploaded thumbnail.
- **MultiImage**: `{"multiImage": {"images": [{"id": "urn:li:image:..", "altText": ".."}, ...], "altText": ".."}}` - minimum 2, maximum 20 images, organic only.
- **Poll**: `{"poll": {"question": "<=140 chars", "options": [{"text": "<=30 chars"}, ... 2 to 4], "settings": {"duration": "ONE_DAY|THREE_DAYS|SEVEN_DAYS|FOURTEEN_DAYS", "voteSelectionType": "SINGLE_VOTE", "isVoterVisibleToAuthor": true}}}`. Organic only, cannot be edited after creation, no political/health/sensitive questions. `isVoterVisibleToAuthor:false` returns 400.
- **Reshare**: add `"reshareContext": {"parent": "urn:li:share:..."}` (root is derived).
- Call-to-action fields (`contentCallToActionLabel`, `contentLandingPage`) are for ads/article posts.

### Read
- `GET /rest/posts/{encoded postUrn}` (add `viewContext=AUTHOR` to see unpublished/draft versions; default `READER`).
- Batch: `GET /rest/posts?ids=List({enc urn},{enc urn})` with header `X-RestLi-Method: BATCH_GET` (not on the Community Management Development tier).
- By author: `GET /rest/posts?q=author&author={enc person or org urn}&count=10&sortBy=LAST_MODIFIED|CREATED`; one author per call, `count` max 100. Listing a **person's** posts needs `r_member_social` (closed); an **organization's** posts need `r_organization_social`. For versions before 202301 only organization authors work.
- By ad account: `q=dscAdAccount&dscAdAccount=...&dscAdTypes=List(STANDARD,VIDEO)`.

### Edit (POST `/rest/posts/{urn}` + header `X-RestLi-Method: PARTIAL_UPDATE`)
Body `{"patch": {"$set": {"commentary": "new text"}}}`. Editable: `commentary`, `contentCallToActionLabel`, `contentLandingPage`, `lifecycleState`, and `adContext.dscName/dscStatus`. Success `204`. Media, visibility and polls cannot be edited.

### Delete (DELETE `/rest/posts/{enc urn}`)
`204`, idempotent. No batch delete.

### Disable comments
Use Social Metadata (below): set `commentsState` to `CLOSED`. This **deletes existing comments**; reopening allows new ones.

## 3. Media upload flows (all give a URN to put in `content.media.id`)
**Image** (`POST /rest/images?action=initializeUpload`, body `{"initializeUploadRequest": {"owner": "urn:li:person:..|urn:li:organization:.."}}`): response `{"value": {"uploadUrl", "uploadUrlExpiresAt", "image": "urn:li:image:..."}}`. Then **PUT** the raw bytes to `uploadUrl` **with the Authorization bearer header**. Limits: under 36,152,320 pixels; JPG, PNG, GIF (GIF up to 250 frames). Check status with `GET /rest/images/{urn}` (`PROCESSING`, `AVAILABLE`, `PROCESSING_FAILED`, `WAITING_UPLOAD`). Images are reusable across posts/ads. Replaces the legacy Assets API (`registerUpload`, `digitalMediaAsset` URNs; `urn:li:digitalMediaAsset:X` maps to `urn:li:image:X`).

**Video** (`POST /rest/videos?action=initializeUpload`, body with `initializeUploadRequest`: `owner`, **`fileSizeBytes` (required)**, optional `uploadCaptions`, `uploadThumbnail`): response has `uploadInstructions` (one entry per part, byte ranges of 4 MB = 4,194,303 bytes each, parts sorted), `uploadToken`, `video` URN, `uploadUrlsExpireAt` (about 30 days). Upload each part with PUT; **the video part upload does not accept an OAuth token**; save each response `ETag`. Then `POST /rest/videos?action=finalizeUpload` with `{"finalizeUploadRequest": {"video": "...", "uploadToken": "...", "uploadedPartIds": [etags in part order]}}`. Limits: MP4, 3 seconds to 30 minutes, 75 KB to 500 MB for ads/feed (API init allows up to 5 GB). One English caption file (SRT) and a thumbnail can be uploaded. Status values as for images; failure reason in `processingFailureReason`. Fields from 202602: `templateName`, `linkbackContext`.

**Document** (`POST /rest/documents?action=initializeUpload`): same pattern as images (PUT bytes to the `uploadUrl`). Limits: **100 MB and 300 pages**; PPT, PPTX, DOC, DOCX, PDF. `media.title` is mandatory when posting a document.

## 4. Text format ("little text") and mentions
`commentary` is one string. Reserved characters must be backslash-escaped to be plain text: `| { } @ [ ] ( ) < > # \ * _ ~`. (Our publisher deliberately leaves `#` unescaped so hashtags stay clickable.)
- Mention: `@[Display Name](urn:li:person:1234)` or `@[Company Name](urn:li:organization:2414183)`. The text must **match the name exactly (case sensitive)** or it shows as plain text; a member mention needs to match only one of their names. Mentionable organizations: companies, schools, brands.
- Hashtag: `{hashtag|\#|mytag}` (HashtagTemplate with the `#` sign escaped) or a plain `#tag`.
- People Typeahead (`posts-atmention-search-api`): lets a Page admin search followers by keyword (up to 10 results) or vanity name to get person URNs for mentions; returns followers only.
- Newlines `\n` work; bullet characters like `*` need escaping.

## 5. Comments (`/rest/socialActions/{shareUrn|ugcPostUrn|commentUrn}/comments`)
- Create: `POST .../comments` body `{"actor": "urn:li:person:..|urn:li:organization:..", "message": {"text": "..."}, "object": "<post urn>"}` (+ optional `parentComment` composite URN for a reply, `content` with an image entity). Response header has the comment id; comment URNs are composite: `urn:li:comment:(urn:li:activity:123,456)`.
- Read: `GET .../comments` (top level for a post, replies for a comment URN), `GET .../comments/{id}`, batch `.../comments/ids=List(...)`.
- Edit: `POST .../comments/{id}` with `actor` when editing as an organization; only text and attributes can change. Delete: `DELETE .../comments/{id}?actor=...`.
- Mentions inside comments use `attributes` with `start`, `length`, `value` (urn).
- Images in a comment: `content` with an `entity` image URN (an inline image comment may return 403 "Unpermitted fields ... /content").
- Throttle: a short per-member creation limit exists (429 "creation rate limit exceeded for member").
- Reading comments on a member's post requires the closed `r_member_social_feed`.

## 6. Reactions (`/rest/reactions`)
- Types: `LIKE` (Like), `PRAISE` (Celebrate), `EMPATHY` (Love), `INTEREST` (Insightful), `APPRECIATION` (Support), `ENTERTAINMENT` (Funny). `MAYBE` (Curious) is **deprecated since 202307** and returns 400.
- React: `POST /rest/reactions?actor={enc person|org urn}` body `{"root": "<post urn>", "reactionType": "LIKE"}` (on a comment: root = the post, entity = comment). `201`.
- Read one: `GET /rest/reactions/(actor:{enc urn},entity:{enc urn})`; read all on a post: `GET /rest/reactions/(entity:{enc urn})?q=entity&sort=(value:REVERSE_CHRONOLOGICAL|CHRONOLOGICAL|RELEVANCE)`; batch via `ids=List((actor:..,entity:..),...)`.
- Remove: `DELETE /rest/reactions/(actor:..,entity:..)` -> `204`.
- Replaces likes in the legacy `socialActions` endpoint.

## 7. Social Metadata (counts for a post)
`GET /rest/socialMetadata/{post or comment urn}` (batch `?ids=List(...)`) returns `commentsState` (OPEN, CLOSED, PROCESSING, DELETED), `commentSummary` (`count` incl. replies, `topLevelCount`), `reactionSummaries` keyed by reaction type with `count`. Needs the `*_social_feed` read scopes - **for a member's posts that is the closed `r_member_social_feed`, so it answers 403 for us**; it works for organization posts with `r_organization_social_feed`. Enable/disable comments: `POST /rest/socialMetadata/{urn}?actor=...` body sets `commentsState` (`202 Accepted`).

## 8. Legacy endpoints you will still meet in old code
- `POST /v2/ugcPosts`, `/v2/shares`, `/v2/assets?action=registerUpload`, `/v2/socialActions/{urn}` (likes + comments) and `/v2/me`. The Posts, Images, Videos, Documents, Reactions, Comments and Social Metadata APIs replace them (migration guide: `contentapi-migration-guide`). Field renames: `owner`->`author`, `specificContent`->`content`, `shareCommentary`->`commentary`, `resharedShare`->`reshareContext.parent`, AuditStamps flattened to `createdAt`, `lastModifiedAt`, etc.
- Find-by-author for **persons** works from version 202301; before that only organizations.
- Share on LinkedIn (UGC) limits: 150 calls/member/day.

## 9. Practical gotchas
- URL-encode post URNs in paths and in `entity=(share:urn%3Ali%3Ashare%3A...)`; never double-encode.
- A 404 `Unable to obtain corresponding activityUrn` on a reactions/comments call usually means the URN type does not match the endpoint (share vs ugcPost vs activity) or the post was deleted.
- A post may exist as both a `share` and a `ugcPost` id; use whichever the create response header gave.
- Posting is asynchronous for media: wait for image/video/document `AVAILABLE` before creating the post, otherwise the post can end `PUBLISH_FAILED`.
- Page-admin role changes can only be made in the LinkedIn UI.
