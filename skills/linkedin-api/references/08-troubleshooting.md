# 08 - Troubleshooting: symptom, cause, fix

Mix of LinkedIn's documented behaviour (marked **docs**) and field notes from building real automation (marked **field**). Field notes are experience, not LinkedIn promises: confirm on the live pages when it matters.

## Sign-in and tokens
| Symptom | Likely cause | Fix |
|---|---|---|
| Authorize page says `unauthorized_scope_error` / "Scope ... is not authorized for your application" | The scope's product is not on the app (docs: scopes come from Products) | Developer Portal -> app -> Products -> add "Sign in with LinkedIn using OpenID Connect" (for `openid profile email`) or "Share on LinkedIn" (for `w_member_social`) |
| "Redirect URI doesn't match" / `invalid_redirect_uri` | The redirect in the request is not character-for-character one registered on the app (scheme, host, port, path, trailing slash) | Register the exact URL in the Auth tab. **docs**: absolute, no `#`, query strings ignored |
| `invalid_request ... authorization code not found / expired` | Code used twice or older than 30 minutes | Start the login again |
| 401 on any call, was working yesterday | Token expired (60 days), revoked by the member, or app secret rotated | Sign in again; check the token with the inspector or introspection |
| Sign-in works but posting returns 403 | Token has no `w_member_social` (scopes changed after consent) | Add the product, sign in again; changing scopes invalidates the old token |
| Community Management option is greyed out on the app | The app already has other products (**docs**: it must be the only product) | Create a new app for it; keep sign-in/posting on the first app (**field**: two-app setup works) |
| Client secret suddenly rejected | It was regenerated/overwritten (**docs**: up to two secrets; new becomes primary, old stays as secondary until removed) | Paste the current primary secret; remove the secondary only after switching |
| Wrong app's credentials in a config slot | Easy with two apps | Name variables per app, for example `LINKEDIN_CLIENT_ID` vs `LINKEDIN_STATS_CLIENT_ID` |

## Calls and limits
| Symptom | Likely cause | Fix |
|---|---|---|
| 400 on `memberCreatorPostAnalytics?q=entity` | The post URN was encoded twice (an HTTP library re-encoded `%3A`) (**field**: this exact mistake produced a burst of 400s) | Build the query string yourself; encode the URN once: `entity=(share:urn%3Ali%3Ashare%3A123)` |
| 429 "throttle limit" with few calls | Member limit is 100 per day on the Development tier and a refresh loop used it up (**field**) | Ask old posts less often, cache for hours, count calls, stop at 90 |
| A burst of calls right after you restart a service | A scheduled refresh runs at start-up (**field**) | Skip the refresh if one ran recently; persist the last-run time |
| 403 on `socialMetadata` or comments for your own personal posts | Reading member social data needs `r_member_social_feed`, a **closed** permission (docs) | Use the reactions finder for like counts, analytics API for views/comments/reposts, or enter numbers manually |
| BATCH_GET returns an error on Development tier | **docs**: no BATCH_GET calls allowed on that tier | Make single calls or upgrade to Standard |
| 426 | Version header retired | Set `Linkedin-Version` to a supported version |
| 404 "Unable to obtain corresponding activityUrn" | URN type does not fit the endpoint, or the post is gone | Use the id from the create response (share vs ugcPost) |
| 414 | URL too long | Query tunneling (file 02) |
| 500 on analytics | **docs**: intermittent, retry | Retry with backoff; log `x-li-request-id` |

## Posting
| Symptom | Likely cause | Fix |
|---|---|---|
| Create returns 201 but no body | Normal | Read the new id from the `x-restli-id` response header |
| Post text shows backslashes or loses formatting | Reserved characters not escaped, or escaped twice | Escape once: `| { } @ [ ] ( ) < > \ * _ ~` (leave `#` for hashtags) |
| A mention shows as plain text | Name text does not match exactly (case sensitive) | Match the member's or company's name exactly |
| Image upload `PUT` returns 401 | **docs**: the image PUT needs the bearer token | Add `Authorization: Bearer ...` to the PUT |
| Video part `PUT` fails with a token | **docs**: the video part upload does not accept an OAuth token | Send the part without Authorization; keep each `ETag` |
| Post ends `PUBLISH_FAILED` | Media was still processing, or invalid | Wait until the asset is `AVAILABLE`; edit and retry |
| Article link shows no preview | **docs**: the Posts API does not scrape links | Send `source`, `title`, `description` and an uploaded `thumbnail` |
| Poll returns 400 | Question over 140 chars, option over 30, fewer than 2 or more than 4 options, or hidden voters | Fix the field limits (file 03) |
| Comments on someone else's post fail | Needs `w_member_social` (person) and a valid post URN type; short per-member comment throttle | Slow down; use the right URN (share, ugcPost or activity) |

## Webhooks
| Symptom | Fix |
|---|---|
| "This URL did not pass the security challenge check" | Reply to the challenge with the hex HMAC-SHA256 of `challengeCode` keyed by the client secret, as JSON `{challengeCode, challengeResponse}` |
| Events stopped | Endpoint failed validation three times in a row and was blocked; fix it and revalidate in the portal |
| Signature check fails | Hash the raw body exactly as received, prefixed with the text `hmacsha256=`, constant-time compare |

## Habits that prevent most of this
Log HTTP status and LinkedIn's request id (never tokens), keep one place for the version header, cache everything you can, count calls, test with a dry run before the first real post, and use a throwaway test post with `CONNECTIONS` visibility the first time.
