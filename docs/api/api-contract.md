# API Contract

This document defines the API endpoints for the Open Projects Hub, intended for frontend integration.

## Base URL

- **Local:** `http://localhost:8000`
- **Docker:** `http://localhost:8080`
- **Production:** `https://api.yourdomain.com`

## API Version

All endpoints are prefixed with `/v1`.

## Authorization

Two roles exist: **Admin** (full CRUD) and **Viewer** (read-only). `Authenticated` below
means either role; `Admin Only` means a Viewer receives 403.

- `401 Unauthorized` — the JWT is missing, malformed, or expired. Authenticate and retry.
- `403 Forbidden` — the JWT is valid but the role is not allowed. Retrying will not help.

## Endpoints Summary

| Method | Path | Authentication | Description |
|---|---|---|---|
| `GET` | `/health` | None | Health check endpoint |
| `POST` | `/v1/auth/login` | None | User login. Returns 403 `{"detail", "code": "EMAIL_NOT_VERIFIED"}` when the password is correct but the email is unverified |
| `POST` | `/v1/auth/register` | None | Bootstraps the instance's first account. Always creates an **Admin**; a `role` field in the body is rejected with 422. Returns 403 once any account exists — later accounts come from `POST /v1/users`. Creates the account unverified, emails a 6-character code, and returns 201 `{email (masked), verificationRequired, nextStep: "verify-email", codeExpiresAt}` with no tokens |
| `POST` | `/v1/auth/verify-email` | None | Body `{email, code, password?}`. Verifies the account and grants its free AI credits (Admins and Members, 5 each, up to 25 per workspace; Viewers none). Accounts added by an Admin send `password` to choose their own; it is checked before the code, so a weak one does not burn an attempt. 400 for an invalid, expired or superseded code; 429 after 5 wrong attempts (request a new code) |
| `POST` | `/v1/auth/resend-verification` | None | Body `{email}`. Emails a new code and invalidates the previous one. Always 200 with a generic message; 429 after 3 resends in 15 minutes |
| `POST` | `/v1/auth/refresh` | None | Refresh access token |
| `GET` | `/v1/users/{user_id}` | Authenticated | Get user by ID |
| `GET` | `/v1/users/me/profile` | Authenticated | Get current user profile |
| `PATCH` | `/v1/users/me/profile` | Authenticated | Update current user profile |
| `POST` | `/v1/users/me/password` | Authenticated | Change password |
| `POST` | `/v1/users` | Admin Only | Add a member or viewer. Body `{displayName, email, role?}`, no password: they get a verification email and set their own. 409 when the workspace already has 5 users (any role, inactive and unverified included) |
| `POST` | `/v1/clients` | Admin Only | Create client |
| `GET` | `/v1/clients` | Admin Only | List clients with pagination |
| `GET` | `/v1/clients/{client_id}` | Admin Only | Get client by ID |
| `PATCH` | `/v1/clients/{client_id}` | Admin Only | Update client |
| `DELETE` | `/v1/clients/{client_id}` | Admin Only | Delete client (409 if active projects exist; archived projects removed as part of deletion) |
| `POST` | `/v1/projects` | Admin Only | Create project (max 3 active projects per admin) |
| `GET` | `/v1/projects` | Authenticated | List projects with pagination and filters (status, clientId, date ranges, search) |
| `GET` | `/v1/projects/{project_id}` | Authenticated | Get project by ID |
| `PATCH` | `/v1/projects/{project_id}` | Admin Only | Update project |
| `POST` | `/v1/projects/{project_id}/archive` | Admin Only | Archive project (frees an active-project slot) |
| `POST` | `/v1/projects/{project_id}/reactivate` | Admin Only | Reactivate archived/completed project (409 if at active limit) |
| `DELETE` | `/v1/projects/{project_id}` | Admin Only | Delete project (404 if not found) |
| `GET` | `/v1/projects/{project_id}/backlog` | Authenticated | Get the approved backlog with acceptance criteria |
| `POST` | `/v1/projects/{project_id}/exports/markdown` | Admin Only | Export the backlog as a Markdown file |
| `POST` | `/v1/stories` | Admin Only | Create story |
| `GET` | `/v1/stories` | Authenticated | List stories with pagination and filters |
| `GET` | `/v1/stories/by-project/{project_id}` | Authenticated | Get stories by project with pagination |
| `GET` | `/v1/stories/{story_id}` | Authenticated | Get story by ID |
| `PATCH` | `/v1/stories/{story_id}` | Admin Only | Update story |
| `DELETE` | `/v1/stories/{story_id}` | Admin Only | Delete story |
| `POST` | `/v1/stories/{story_id}/assign` | Admin Only | Assign story to user |
| `POST` | `/v1/refinement/generate-stories` | Admin Only | Generate refined stories from notes using AI (nothing is stored) |
| `POST` | `/v1/refinement/approve-story` | Admin Only | Approve one refined story; it is saved to the backlog |
| `POST` | `/v1/refinement/approve-stories` | Admin Only | Approve several refined stories; saved to the backlog |
| `GET` | `/v1/dashboard/stats` | Authenticated | Get dashboard statistics |

## General Conventions

- **JSON Convention:** All request and response bodies use `camelCase` for JSON field names.
- **Authentication:** JWT (JSON Web Tokens) in `Authorization: Bearer <token>` header.
- **Rate Limiting:** Applied per IP address.
- **Error Responses:** Consistent JSON format `{"detail": "Error message"}`.
- **Content Type:** All requests and responses use `application/json`.
- **Date/Time Format:** ISO 8601 format with UTC timezone (e.g., `2026-04-30T17:00:00.000Z`).
- **UUIDs:** All entity IDs use UUID v4 format.
- **Pagination:** Offset-based with `limit` and `offset` query parameters.

## Story Refinement

Refined stories are never persisted. `POST /v1/refinement/generate-stories` returns them
(`title`, `description`, `acceptanceCriteria`, no `id`) and the client holds them while the
Admin edits or discards them. A story is written to `stories` only when approved, by sending
its content back:

- `POST /v1/refinement/approve-story` — body `{projectId, title, description?, acceptanceCriteria?}`; returns the created story.
- `POST /v1/refinement/approve-stories` — body `{stories: [<same shape>]}`; returns `{approvedCount, stories: [{id, title}]}`. A project outside the caller's workspace or an invalid story rejects the whole batch before anything is saved.

Because nothing is stored server-side, the API cannot detect a repeated approval: approving the
same content twice creates two stories, so clients must prevent double submits.

Status codes: `200`, `401`, `403`, `404` (project not in the caller's workspace), `422`; generation also returns `502` on provider failure.

## Backlog and Markdown Export

### `GET /v1/projects/{project_id}/backlog`

Returns the project's approved backlog: each story with its title, body and acceptance
criteria. Available to Admin and Viewer.

Unapproved work is excluded structurally rather than by a filter — refined stories are
never stored; they reach the `stories` table only when an Admin approves them. Stories are
ordered for reading: highest priority first, then oldest first, so the view and the export
present the same sequence.

Query parameters: `limit` (default 50, max 100), `offset` (default 0). The response uses the
standard pagination envelope; each item carries `acceptanceCriteria` and omits the internal
`assignedTo` / `createdBy` fields.

Status codes: `200`, `401`, `404`, `422`

### `POST /v1/projects/{project_id}/exports/markdown`

Generates the Markdown artifact from the same backlog and returns it as a file download.
Admin only: a Viewer may read the backlog but not export it (FR-004-05).

Request body (all fields optional; an absent body exports the whole backlog). Unknown fields
are rejected, so a misspelled filter fails loudly instead of silently widening the scope:

```json
{
  "status": "todo | in_progress | blocked | done",
  "dateFrom": "2026-01-01",
  "dateTo": "2026-06-30"
}
```

`status` filters the story lifecycle, not the approval state — every story in this table is
approved by definition. `dateFrom` / `dateTo` are inclusive calendar days applied to
`createdAt`; an inverted range is rejected with `422` rather than exporting nothing.

Response: `200` with the document itself, not a JSON envelope.

```
Content-Type: text/markdown; charset=utf-8
Content-Disposition: attachment; filename="acme-portal-backlog-2026-09-20.md"
X-Export-Story-Count: 12
X-Export-Warning: No approved stories match this scope.   (only when the count is 0)
Access-Control-Expose-Headers: Content-Disposition, X-Export-Story-Count, X-Export-Warning
```

An empty scope is warned about rather than refused (FR-004-06): the caller still receives a
header-only template and decides whether to keep it. The filename is the slugified project
name plus the generation date, reduced to ASCII word characters and hyphens so a project name
cannot shape the header or the saved path.

A single export is capped at 1000 stories, because it is one document a person reads rather
than a paged feed. A scope that exceeds the cap is not silently truncated: the document holds
the first 1000 and `X-Export-Warning` names the full match count and how to narrow the scope.

**Mixed acceptance-criteria formatting in older projects.** Stories approved before the
`acceptance_criteria` column existed keep their criteria inside `description`, as the
`**Acceptance Criteria:**` block the refinement approval mapper used to write, and their
`acceptanceCriteria` array is empty. The migration deliberately does not backfill them, since
that would mean parsing free text an Admin may since have edited. An export spanning both eras
therefore renders older stories' criteria as body text and newer ones under a proper
`### Acceptance Criteria` heading. Re-approving, or editing the story to populate
`acceptanceCriteria`, normalizes it.

Status codes: `200`, `401`, `403`, `404`, `422`

**Deviation from the architecture docs.** `docs/03-architecture/api/api-contract.md` in the
docs repo describes this endpoint as an async S3 upload returning `201 {exportId, downloadUrl}`,
with a companion `GET /projects/{projectId}/exports/{exportId}`. The MVP returns the file
synchronously instead: there is no export bucket, no `exports` table — `database-design.md`
explicitly dropped export tracking for MVP — and nothing to poll. The companion retrieval
endpoint does not exist.
