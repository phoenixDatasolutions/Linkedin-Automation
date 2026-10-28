# 05 - Sign in with LinkedIn, Share on LinkedIn, plugins and the consumer products

Sources: `consumer/integrations/self-serve/sign-in-with-linkedin-v2`, `.../share-on-linkedin`, `.../plugins`, `.../migration-faq`, `consumer/integrations/verified-on-linkedin/*`, `consumer/integrations/live-video/*`, `consumer/integrations/scores-reviews-3p-signals/*`, root `consumer`.

## Sign in with LinkedIn using OpenID Connect (open product)
- Add the product "Sign in with LinkedIn using OpenID Connect" on the app. Scopes: `openid` (required), `profile` (name, picture, id), `email`.
- Run the normal authorization code flow (file 01) with those scopes. You receive an access token **and an ID token** (a JWT: `iss` = https://www.linkedin.com, `sub` = member id, `aud` = your client id, `iat`, `exp`). Validate the ID token with the discovery document `https://www.linkedin.com/oauth/.well-known/openid-configuration` and the keys at `https://www.linkedin.com/oauth/openid/jwks`.
- Or call `GET https://api.linkedin.com/v2/userinfo` with the bearer token: `sub`, `name`, `given_name`, `family_name`, `picture`, `locale`, and optionally `email`, `email_verified` (handle their absence).
- The person URN for posting is `urn:li:person:{sub}`.
- It does **not** verify identity and must not be marketed as doing so.
- Old names (`r_liteprofile`, `r_emailaddress`, `r_basicprofile`, `w_share`) are v1/v2-era; `w_member_social` replaced `w_share`.

## Share on LinkedIn (open product) - posting as a member
- Add the product "Share on LinkedIn" -> scope `w_member_social`.
- The docs still show the legacy UGC API: `POST https://api.linkedin.com/v2/ugcPosts` with `X-Restli-Protocol-Version: 2.0.0`, body `author` (person URN), `lifecycleState: "PUBLISHED"`, `specificContent.com.linkedin.ugc.ShareContent` { `shareCommentary.text`, `shareMediaCategory` NONE | ARTICLE | IMAGE | VIDEO, `media[]` with `status: "READY"`, `originalUrl`, `title`, `description`, or an asset URN }, `visibility.com.linkedin.ugc.MemberNetworkVisibility` PUBLIC | CONNECTIONS. `201` with the id in `X-RestLi-Id`.
- Images/videos: register upload at `/v2/assets?action=registerUpload` (recipe `feedshare-image` / `feedshare-video`), upload binary to the returned URL, use the asset URN.
- **Rate limits (legacy page): 150 requests per member per day, 100,000 per app.**
- New builds should use the **Posts API** (`/rest/posts`, file 03), which accepts the same `w_member_social` token.

## Plugins (no API key)
JavaScript snippets for a website: **Share plugin** and **Follow Company plugin** (plus AutoFill). Governed by the Plugins Terms of Use. They are the zero-approval way to let a visitor share a page or follow a Company Page.

## Other consumer-side programs (all gated)
- **Verified on LinkedIn**: signals that a member verified identity (government ID) or workplace email; endpoints `/identityMe`, `/validationStatus`, `/verificationReport`; Development, Lite and Plus tiers; for trust & safety, communities and marketplaces; not for lead-gen or sales.
- **Live Events API** (beta, apply to broadcast): register an event, ingest RTMP, create the post, end the event, check status. Member or Page scopes cannot be combined in one authorization.
- **Scores, Reviews and 3P Signals**: closed beta, invitation only; partners write credibility signals to member profiles' Apps section (`/credibilitySignalV2`, `/profileComponents`, `/profileDocuments`, `/profileImages`).
- **Add to Profile** (https://addtoprofile.linkedin.com/): a link generator for certifications, no API.

## Which path should a builder pick?
| I want to... | Use |
|---|---|
| Let someone sign in with LinkedIn | OpenID Connect product (instant) |
| Post to my own profile from my software | Share on LinkedIn (`w_member_social`) + Posts API (instant) |
| Read my post numbers | Community Management API, Development tier (review; must be the only product on its own app) |
| Post to or read a Company Page | Community Management API (review) and a Page role |
| Put a share/follow button on a site | Plugins |
