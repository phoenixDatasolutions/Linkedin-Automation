# Setup guide: from nothing to your first LinkedIn post

About 15 minutes. You will create a free LinkedIn developer app, give it two instant products, store its keys privately, sign in once, and post. Every step has a "you should see" line so you know it worked.

> **Golden rule:** your client secret and tokens never go into chat, a repository, a screenshot or an email. The commands below store them in a private file on your own computer.

## What you need
- A LinkedIn account (yours) and the ability to create a LinkedIn **Page** (free).
- A computer with **Python 3.9 or newer** and a terminal. Check with `python3 --version`.
- Claude Code, Claude Desktop or claude.ai with Skills (Claude walks you through this guide, but you can also follow it alone).

## Step 1 - Install the commands
```bash
pipx install git+https://github.com/phoenixDatasolutions/Linkedin-Automation
li-auth check
```
No pipx? `python3 -m pip install --user git+https://github.com/phoenixDatasolutions/Linkedin-Automation`.
**You should see:** two lines saying `MISSING LINKEDIN_CLIENT_ID` and `MISSING LINKEDIN_CLIENT_SECRET`. That is correct: you have not added them yet.

## Step 2 - A LinkedIn Page
LinkedIn only lets a developer app be tied to a Company Page. If you have none: on linkedin.com open **For Business > Create a Company Page**. A small page is fine; use your real business name or a page you own. You must be its administrator.

## Step 3 - Create the developer app
1. Open <https://www.linkedin.com/developers/apps/new>.
2. **App name:** anything. **LinkedIn Page:** the page from step 2. **Privacy policy URL:** your website's, if asked. **App logo:** any square image.
3. Tick the legal box and **Create app**.
4. Open the app's **Settings** tab and click **Verify** next to your Page; approve it as the Page admin.
**You should see:** "Verified" next to the Page.

## Step 4 - Add the two instant products
Open the **Products** tab and click **Request access** on:
- **Share on LinkedIn** - gives the `w_member_social` permission (post as you).
- **Sign in with LinkedIn using OpenID Connect** - gives `openid`, `profile`, `email` (who you are).

**You should see:** both under "Added products", and on the **Auth** tab the scopes `openid`, `profile`, `w_member_social` listed.
If the scopes are missing, the product was not added. Without them LinkedIn shows `unauthorized_scope_error`.

## Step 5 - Redirect URL and your keys
1. **Auth** tab, **Authorized redirect URLs for your app**: add `http://localhost:8765/callback` and save.
   If LinkedIn does not accept `http`, add `https://oauth.pstmn.io/v1/callback` instead and use `--redirect https://oauth.pstmn.io/v1/callback --manual` in step 6.
2. On the same tab copy the **Client ID** and show the **Primary Client Secret** (eye icon).
3. In your terminal:
   ```bash
   li-auth setup
   ```
   Paste the Client ID, press Enter, then paste the secret (it is hidden as you type).
**You should see:** `Saved to ~/.config/linkedin-automation/.env (owner-only)`. Run `li-auth check` again: both lines say `OK`.

## Step 6 - Sign in
```bash
li-auth login
```
A browser tab opens with LinkedIn's permission screen. Click **Allow**. The terminal says `Signed in as: urn:li:person:...`.
If the browser does not return to the terminal, copy the whole address from the address bar (even if it shows an error page) and paste it when asked.
`li-auth status` shows how many days are left. The token lasts about 60 days; run `li-auth login` again when it ends.

## Step 7 - Dry run
```bash
li-post text "Testing my new LinkedIn automation."
```
**You should see:** a post check, the exact JSON that would be sent, and `DRY RUN: nothing was sent`.

## Step 8 - One real post (optional)
Use a test with limited visibility first:
```bash
li-post text "Testing my new LinkedIn automation." --visibility CONNECTIONS --publish
```
Type `publish` when asked. The link is printed. Delete the test if you like: `li-post delete <urn> --publish` (the URN is in the printed link).

## Step 9 - Let Claude write for you
In Claude: *"Build my voice profile"* (the `linkedin-writer` skill asks for 5-10 of your past posts, or interviews you), then *"Write a post about ..."*. Claude drafts, runs `li-lint`, shows you the exact text, and only publishes after you say yes (`linkedin-publisher`).

## Optional A - Schedule posts
LinkedIn's API cannot "publish later", so this toolkit keeps a queue:
```bash
li-schedule add post.txt --at "2026-11-03 09:30" --tz Europe/London
li-schedule list
li-schedule approve <id>       # your yes
li-schedule cron               # prints the crontab line (every 5 minutes)
```
Add that line with `crontab -e`. Unapproved items never publish; the cap is 2 posts a day (`LI_SCHEDULE_DAILY_CAP`).

## Optional B - Read your numbers
1. Create a **second** developer app (steps 2-3). The Community Management API must be the *only* product on its app.
2. **Products** tab: request **Community Management API** (Development tier). LinkedIn asks for a business email, your registered organization, website, and a use case, and a Page admin must verify the app. Approval takes days to weeks and is for registered organizations with commercial use cases.
3. Keep the second app's keys apart from the first:
   ```bash
   export LINKEDIN_AUTOMATION_HOME=~/.config/linkedin-automation-stats
   li-auth setup
   li-auth login --scopes "openid profile r_member_postAnalytics r_member_profileAnalytics"
   li-stats budget
   li-stats me --metric IMPRESSION --days 30
   ```
4. **Calendar reminder:** Development tier access is removed after 12 months unless you apply for Standard tier.

## Windows and Mac notes
- **Mac / Linux:** works as written. **Windows:** use WSL, or PowerShell with `py -m pip install --user ...`; file permissions (owner-only) are best-effort on Windows, so keep the config folder in your user profile only.
- Config folder: `~/.config/linkedin-automation/` (or `$LINKEDIN_AUTOMATION_HOME`, or `$XDG_CONFIG_HOME/linkedin-automation/`).

## If something goes wrong
| You see | Fix |
|---|---|
| `unauthorized_scope_error` | Add the product (step 4), then log in again |
| "redirect_uri doesn't match" | The URL in step 5 must equal the one used, character for character |
| `The 'state' did not match` | Start `li-auth login` again and use the same browser |
| `401` | Token expired or revoked: `li-auth login` |
| `403` on posting | Missing `w_member_social`; add Share on LinkedIn and log in again |
| `429` | A daily limit; try after midnight UTC |
More: [`skills/linkedin-api/references/08-troubleshooting.md`](../skills/linkedin-api/references/08-troubleshooting.md).
