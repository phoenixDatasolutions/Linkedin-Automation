---
name: linkedin-api-setup
description: Guided, step-by-step setup to connect Claude to LinkedIn's official API - create a LinkedIn Page and developer app, add the right products, get the client ID and secret (the "API key"), sign in with OAuth, and make a first safe test post. Use when someone says "set up LinkedIn automation", "get a LinkedIn API key", "connect Claude to LinkedIn", "authorize LinkedIn", or hits an OAuth error.
---

# LinkedIn API setup wizard

Goal: from nothing to "Claude can draft, and after my approval publish, to my LinkedIn" in about 15 minutes, using only LinkedIn's official API.

## Rules for you (Claude) while running this
- **Never ask the user to paste the client secret, a token or a password into the chat.** Tell them to run `li-auth setup` in their own terminal (the secret is typed hidden and saved to a private file).
- Do one step at a time. After each step ask them to confirm (or paste an error) before the next.
- Explain plainly: "API key" in LinkedIn language = *Client ID + Client Secret* of a developer app.
- If a step fails, open `linkedin-api/references/08-troubleshooting.md` and use the matching row.
- Do not publish anything real during setup except the optional test post in step 8, and only with their yes.

## Step 0 - choose the path
| You want | Path | Review needed? |
|---|---|---|
| Post to your own profile from Claude | **A: personal posting** | No, instant |
| Also read views, comments, reposts of your posts | **B: add analytics** (second app, Community Management API) | Yes (days to weeks), must be a registered organization |
| Post as a Company Page | **B** too (`w_organization_social` + you must be a Page admin) | Yes |
Start with A. B can be added later.

## Step 1 - install the toolkit
```bash
pipx install git+https://github.com/phoenixDatasolutions/Linkedin-Automation   # or: pip install --user git+https://...
li-auth check          # shows what is missing; nothing secret is printed
```
Requires Python 3.9+. No other packages are installed.

## Step 2 - a LinkedIn Page (required to create an app)
LinkedIn only lets a developer app be linked to a Company Page. If you have none: LinkedIn -> Work -> Create a Company Page (a small "company" or "solo business" page is fine; use your real business or a page you own).

## Step 3 - create the developer app
1. Open https://www.linkedin.com/developers/apps/new and sign in.
2. App name (anything), LinkedIn Page = your page, privacy policy URL (if asked, your website's), logo (any square image).
3. Create the app. Then on the app's **Settings** tab click **Verify** next to the Page and have a Page super admin approve (you, if you made the Page).

## Step 4 - add the products
App -> **Products** tab -> request:
- **Share on LinkedIn** (gives `w_member_social`, instant)
- **Sign in with LinkedIn using OpenID Connect** (gives `openid`, `profile`, `email`, instant)
Open the **Auth** tab and check these scopes are listed. If not, the product was not added.

## Step 5 - redirect URL and credentials
1. Auth tab -> **Authorized redirect URLs for your app** -> add `http://localhost:8765/callback` and save. (If LinkedIn refuses `http`, add `https://oauth.pstmn.io/v1/callback` instead and use `--redirect https://oauth.pstmn.io/v1/callback --manual` in step 6.)
2. Still on the Auth tab, find **Client ID** and **Primary Client Secret** (click the eye icon).
3. In **your own terminal** run `li-auth setup` and paste them when asked. The secret is hidden. They are saved to `~/.config/linkedin-automation/.env` (owner-only). Never into a repository, never into chat.

## Step 6 - sign in
```bash
li-auth login
```
A browser tab opens, approve access. The terminal prints "Signed in as urn:li:person:...". The token lasts about 60 days; `li-auth status` shows the days left. Re-run `li-auth login` when it expires.
Common errors: `unauthorized_scope_error` = the product from step 4 is missing; "redirect_uri doesn't match" = the URL differs by even one character from step 5.

## Step 7 - dry run
```bash
li-post text "Testing my new LinkedIn automation."
```
Nothing is sent. It checks the text and prints exactly what would be published.

## Step 8 - one real test post (optional, needs the user's explicit yes)
```bash
li-post text "Testing my new LinkedIn automation." --visibility CONNECTIONS --publish
```
They must type the word `publish`. Check LinkedIn, then delete it: `li-post delete <urn> --publish`. (The URN is printed after publishing.)

## Step 9 (path B) - analytics app
1. Create a **second** app (steps 2-3). Community Management must be the only product on its app.
2. Products tab -> **Community Management API** -> request Development tier. LinkedIn asks for a business email, your registered organization, website and a use case; a Page super admin must verify the app.
3. When approved, the Auth tab shows `r_member_postAnalytics` (and others).
4. Use a separate credentials folder so the two apps never mix:
```bash
export LINKEDIN_AUTOMATION_HOME=~/.config/linkedin-automation-stats
li-auth setup
li-auth login --scopes "openid profile r_member_postAnalytics r_member_profileAnalytics"
li-stats budget
```
5. Mark your calendar: Development tier access is **removed after 12 months** unless you apply for Standard.

## You are done when
`li-auth status` shows days left, `li-post text "..."` shows a clean dry run, and (optionally) a test post appeared and was deleted. Next: `linkedin-writer`, then `linkedin-publisher`.
