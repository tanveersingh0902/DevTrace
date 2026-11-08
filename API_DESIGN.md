# DevTrace API Design

**Base path:** `/api/v1`
**Format:** HTTPS JSON, UTF-8
**Status:** Design contract. Phase 1 implements only `/health`, `/ready`, and `/api/v1` metadata.

## Conventions

- JSON uses `snake_case`; IDs are UUID strings; dates are RFC 3339 UTC.
- Protected calls use `Authorization: Bearer <access-token>`.
- Lists use opaque `cursor` and `limit` (default 50, maximum 100), returning `items` and
  `next_cursor`.
- Clients may send `X-Request-ID`; APIs return it. Duplicate-creating mutations accept an
  `Idempotency-Key`.
- Graph calls require bounded depth, filters, and node/edge limits; unbounded traversal is
  rejected.
- Errors use problem-details fields: `type`, `title`, `status`, `detail`, `code`,
  `request_id`, and validation `errors` where applicable. Never expose stack traces,
  secrets, raw source, provider errors, or account-existence clues.

## Endpoint plan

| Method | Path | Access | Purpose |
| --- | --- | --- | --- |
| `GET` | `/health` | Deployment restricted | Liveness without sensitive details |
| `GET` | `/ready` | Deployment restricted | Readiness/database check |
| `POST` | `/auth/register` | Public | Create a local account |
| `POST` | `/auth/login` | Public | Return access token and set refresh cookie |
| `POST` | `/auth/refresh` | Refresh cookie + CSRF | Rotate session and return access token |
| `POST` | `/auth/logout` | Refresh cookie + CSRF | Revoke current session and clear cookie |
| `GET` | `/auth/me` | Authenticated | Read current user |
| `POST` | `/auth/change-password` | Authenticated | Change password and revoke other sessions |
| `GET`, `POST` | `/projects` | Authenticated | List/create projects |
| `GET`, `PATCH` | `/projects/{project_id}` | Viewer / Editor | Read/update project |
| `GET`, `POST` | `/projects/{project_id}/members` | Viewer / Owner | List/add or change membership |
| `DELETE` | `/projects/{project_id}/members/{user_id}` | Owner | Remove member |
| `GET`, `POST` | `/projects/{project_id}/repository-sources` | Viewer / Editor | List/register safe source metadata |
| `PATCH` | `/projects/{project_id}/repository-sources/{source_id}` | Editor | Update safe source configuration |
| `GET`, `POST` | `/projects/{project_id}/analysis-runs` | Viewer / Editor | List/create queued run (`202`) |
| `GET` | `/projects/{project_id}/analysis-runs/{run_id}` | Viewer | Run status/counts |
| `POST` | `/projects/{project_id}/analysis-runs/{run_id}/cancel` | Editor | Request cancellation (`202`) |
| `GET` | `/projects/{project_id}/analysis-runs/{run_id}/summary` | Viewer | Architecture/diagnostic summary |
| `GET` | `/projects/{project_id}/analysis-runs/{run_id}/files` | Viewer | Paginated file inventory |
| `GET` | `/projects/{project_id}/analysis-runs/{run_id}/files/{file_id}` | Viewer | File declarations/diagnostics |
| `GET` | `/projects/{project_id}/analysis-runs/{run_id}/symbols` | Viewer | Searchable symbols |
| `GET` | `/projects/{project_id}/analysis-runs/{run_id}/symbols/{symbol_id}` | Viewer | Symbol details/relationships |
| `GET` | `/projects/{project_id}/analysis-runs/{run_id}/graph` | Viewer | Bounded React Flow projection |
| `GET` | `/projects/{project_id}/analysis-runs/{run_id}/graph/nodes/{node_id}/neighbors` | Viewer | Paged inbound/outbound neighborhood |
| `POST`, `GET` | `/projects/{project_id}/analysis-runs/{run_id}/ai/conversations` | Viewer | Create/list snapshot-scoped threads |
| `GET` | `/projects/{project_id}/ai/conversations/{conversation_id}` | Viewer | Read scoped conversation |
| `POST` | `/projects/{project_id}/ai/conversations/{conversation_id}/messages` | Viewer | Ask grounded question |

## Behavior details

Project responses include ID, name, slug, description, current role, and timestamps.
Analysis runs include source reference, status, snapshot identity, analyzer version, counts,
timestamps, and safe failure information. File/symbol/node/edge responses include run-scoped
identity, display data, and applicable provenance/evidence.

Analysis creation body contains `repository_source_id` and optional ref and requires an
idempotency key. The response is the polling resource; clients back off after terminal
state. Supported repository source types are not promised until implemented safely.

Explorer routes require a completed run and otherwise return `409 analysis_not_complete`.
`GET /graph` supports `center_node_id`, `depth` (initially 1–3), `direction`, relationship/
node filters, and `max_nodes`/`max_edges`. Responses identify applied limits and
`truncated`, so the UI never misrepresents a partial projection as the whole graph.

AI message creation accepts `content` and optional `selected_node_ids`; selected IDs must
belong to the conversation run. The response contains assistant content plus navigable
citations (`node_id`, `file_id`, line range). The first release is non-streaming. Provider
failures have safe retryable/non-retryable codes and no provider internals.

## Browser authentication and communication

One typed Axios client adds base URL, headers, request ID, and in-memory bearer token. On a
`401`, it serializes at most one refresh operation and retries the original request once;
refresh failure clears client auth and routes to login. Access tokens never go in local or
session storage or URLs.

Access tokens are short-lived JWT JSON responses. Refresh tokens are opaque, server-hashed,
rotated `HttpOnly`, `Secure`, `SameSite` cookies scoped to the refresh endpoint. Login uses
generic failures to prevent enumeration. Additive API fields are compatible; breaking
changes get a new version prefix. FastAPI OpenAPI becomes the authoritative machine-readable
contract after Phase 1.
