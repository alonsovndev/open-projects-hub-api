# API Contract

This document defines the API endpoints for the Open Projects Hub, intended for frontend integration.

## Base URL

- **Local:** `http://localhost:8000`
- **Docker:** `http://localhost:8080`
- **Production:** `https://api.yourdomain.com`

## API Version

All endpoints are prefixed with `/v1`.

## Endpoints Summary

| Method | Path | Authentication | Description |
|---|---|---|---|
| `GET` | `/health` | None | Health check endpoint |
| `POST` | `/v1/auth/login` | None | User login |
| `POST` | `/v1/auth/register` | None | Public registration |
| `POST` | `/v1/auth/refresh` | None | Refresh access token |
| `GET` | `/v1/users/{user_id}` | Authenticated | Get user by ID |
| `GET` | `/v1/users/me/profile` | Authenticated | Get current user profile |
| `PATCH` | `/v1/users/me/profile` | Authenticated | Update current user profile |
| `POST` | `/v1/users/me/password` | Authenticated | Change password |
| `POST` | `/v1/users` | Admin Only | Create user |
| `POST` | `/v1/clients` | Admin Only | Create client |
| `GET` | `/v1/clients` | Authenticated | List clients with pagination |
| `GET` | `/v1/clients/{client_id}` | Authenticated | Get client by ID |
| `PUT` | `/v1/clients/{client_id}` | Admin Only | Update client |
| `DELETE` | `/v1/clients/{client_id}` | Admin Only | Delete client |
| `POST` | `/v1/projects` | Admin Only | Create project |
| `GET` | `/v1/projects` | Authenticated | List projects with pagination and optional status filter |
| `GET` | `/v1/projects/{project_id}` | Authenticated | Get project by ID |
| `PATCH` | `/v1/projects/{project_id}` | Admin Only | Update project |
| `DELETE` | `/v1/projects/{project_id}` | Admin Only | Delete project |
| `POST` | `/v1/stories` | Authenticated | Create story |
| `GET` | `/v1/stories` | Authenticated | List stories with pagination and filters |
| `GET` | `/v1/stories/by-project/{project_id}` | Authenticated | Get stories by project with pagination |
| `GET` | `/v1/stories/{story_id}` | Authenticated | Get story by ID |
| `PATCH` | `/v1/stories/{story_id}` | Authenticated (Owner or Admin) | Update story |
| `DELETE` | `/v1/stories/{story_id}` | Authenticated (Owner or Admin) | Delete story |
| `POST` | `/v1/stories/{story_id}/assign` | Authenticated | Assign story to user |
| `PATCH` | `/v1/refinement/drafts/{draft_id}` | Admin Only | Update story draft |
| `POST` | `/v1/refinement/generate-stories` | Admin Only | Generate story drafts from notes using AI |
| `POST` | `/v1/refinement/drafts/{draft_id}/approve` | Admin Only | Approve draft to story |
| `POST` | `/v1/refinement/approve-drafts` | Admin Only | Bulk approve drafts |
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
