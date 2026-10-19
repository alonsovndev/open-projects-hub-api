# Changelog

All notable changes to the API are recorded here. Versions are the `vX.Y.Z` tags on `main`; the format follows [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

Changes on `dev` since `v0.1.0` are listed in the pull requests of this repository.

## [0.1.0] - 2026-10-15

First release. It runs in the current production stack at `https://api-oph.alonsovndev.com` (deployed there on 2026-10-19; see the infrastructure repository).

### Added

- Workspace-scoped clients, projects and stories, with project archive and reactivate and the active-project limit.
- Authentication with JWT access tokens and single-use rotating refresh tokens, account lockout, email verification at sign-up, and password reset by emailed code.
- Open self sign-up: each registration creates its own workspace with an administrator; administrators add members, activate or deactivate them and delete them; workspace rename.
- AI-assisted refinement of raw notes into user stories with acceptance criteria, approval before anything is stored, input sanitization, and failure recovery.
- AI credits per user and user-supplied provider keys (Gemini, OpenAI, DeepSeek), encrypted at rest.
- Approved-backlog view and Markdown export.
- Account-free Client Review through a project access code.
- Production stack: Docker Compose with Caddy, the API and PostgreSQL on one host behind Cloudflare, and a tag-driven workflow that publishes the image to GHCR (`scripts/deploy-release.sh` deploys it).

### Security

- Browser sessions keep the refresh token in an `HttpOnly; Secure; SameSite=Lax` cookie scoped to `/v1/auth`.
- Refresh tokens are rejected as bearer tokens; every workspace route and repository query is scoped to the caller's workspace.
- Security headers (CSP, `X-Frame-Options`, `X-Content-Type-Options`, HSTS in production) and per-endpoint rate limits.

[Unreleased]: https://github.com/alonsovndev/open-projects-hub-api/compare/v0.1.0...dev
[0.1.0]: https://github.com/alonsovndev/open-projects-hub-api/releases/tag/v0.1.0
