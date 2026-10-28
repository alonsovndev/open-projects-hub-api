# Changelog

All notable changes to the API are recorded here. Versions are the `vX.Y.Z` tags on `main`; the format follows [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

## [0.2.0] - TBD

### Added

- First-use onboarding state (F-005): `users.onboarding_completed_at` (migration `0002`), `onboardingCompleted` on the user profile, and `PATCH /v1/users/me/onboarding` to dismiss or replay the welcome. The migration marks existing accounts as already onboarded.

### Changed

- Verification and password-reset emails are retried up to 3 times with exponential backoff on connection and timeout errors (NFR-X10).
- At most 10 verification codes and 10 reset codes can be issued per account per hour, on top of the existing limit per 15 minutes (NFR-X10).
- Version is now `0.2.0` in `pyproject.toml` and the app config; it previously read `1.0.0` while the release tags were `v0.1.x`.

### Documentation

- Python code blocks in the Markdown documentation are formatted with ruff.
- The committed OpenAPI schema includes the onboarding endpoint.

## [0.1.2] - 2026-10-19

### Fixed

- Each 500 error is reported to Sentry once, and events are scrubbed before they are sent.

## [0.1.1] - 2026-10-19

### Security

- Upgrade `pyjwt` 2.10.1 to 2.15.1 and `cryptography` 46.0.7 to 50.0.2 to pick up the published fixes (JWT verification and bundled OpenSSL). The 1026 unit tests pass; the integration tests were not run.

### Changed

- The release image is built in CI and deployed from a workstation with `scripts/deploy-release.sh`; the deployment guide documents the script and rollback.
- Documentation corrected for production: security and coverage notes, missing endpoints and auth requirements in the API reference, and README and setup guides.

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

[Unreleased]: https://github.com/alonsovndev/open-projects-hub-api/compare/v0.2.0...dev
[0.2.0]: https://github.com/alonsovndev/open-projects-hub-api/compare/v0.1.2...v0.2.0
[0.1.2]: https://github.com/alonsovndev/open-projects-hub-api/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/alonsovndev/open-projects-hub-api/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/alonsovndev/open-projects-hub-api/releases/tag/v0.1.0
