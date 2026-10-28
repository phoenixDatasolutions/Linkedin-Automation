# Changelog

## 0.1.0 - 2026-10-29
First release.
- Skills: `linkedin-api` (10-guide knowledge base, docs snapshot 2026-10-29, API 202610), `linkedin-api-setup`, `linkedin-writer`, `linkedin-post-check`, `linkedin-publisher`, `linkedin-comments`, `linkedin-planner`, `linkedin-analytics`.
- Commands: `li-auth` (setup, login, status, logout), `li-post` (text, image, multi-image, document, poll, article, first comment, delete; dry run by default), `li-lint`, `li-stats` (post, me, followers, budget; call counter and cache), `li-schedule` (approval-gated queue with daily cap), `li-secrets-scan`.
- Tests with mocked HTTP; CI with secret scan.

Not yet built: video posts, Company Page analytics commands, webhook receiver, refresh-token support for approved partners.
