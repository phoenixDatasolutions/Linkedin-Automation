# Security

## Reporting a problem
Open a GitHub issue titled "security" with a description that contains **no secrets**, or use GitHub's private vulnerability reporting on this repository if it is enabled.

## Never post these in an issue, pull request or chat
LinkedIn client secrets, access or refresh tokens, authorization codes, passwords, SSH keys, `.env` files, or screenshots that show them. If you did, **rotate them immediately**: LinkedIn Developer Portal, your app, Auth tab, "Generate a new client secret", then remove the old one; sign out of the app in LinkedIn settings to revoke tokens.

## How this project protects your secrets
- Credentials are read from environment variables or `~/.config/linkedin-automation/.env`; they are never part of the repository (`.gitignore` blocks `.env`, `token.json`, keys).
- Files holding secrets are created owner-only (0600) in an owner-only folder (0700).
- Output and logs pass through a redactor that hides tokens, bearer headers, and configured secrets.
- `li-secrets-scan` blocks commits (pre-commit hook via `li-secrets-scan --install-hook`) and runs in CI on every push and pull request.
- Publishing requires a dry run first and an explicit confirmation; scheduled posts require a recorded approval.

## Scope
This tool talks only to `api.linkedin.com` and `www.linkedin.com`. It does not collect telemetry.
