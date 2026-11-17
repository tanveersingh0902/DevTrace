# DevTrace API Design

**Base path:** `/api/v1`
**Format:** HTTPS JSON, UTF-8
**Status:** `/health`, `/ready`, `/api/v1` metadata, and `/api/v1/auth/register` are
implemented. All other feature endpoints below remain planned.

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
  secrets, raw source, or provider errors. Login failures must not reveal whether an
  account exists; the registration duplicate-status tradeoff is documented below.

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
| `GET`, `PATCH` | `/projects/{project_id}` | Viewer / Admin | Read/update project |
| `DELETE` | `/projects/{project_id}` | Owner | Delete project (retention rules apply) |
| `GET`, `POST` | `/projects/{project_id}/members` | Viewer / Admin | List/add or change membership |
| `DELETE` | `/projects/{project_id}/members/{user_id}` | Admin | Remove member within role restrictions |
| `GET`, `POST` | `/projects/{project_id}/repository-sources` | Viewer / Admin | List/register safe source metadata |
| `PATCH` | `/projects/{project_id}/repository-sources/{source_id}` | Admin | Update safe source configuration |
| `GET`, `POST` | `/projects/{project_id}/analysis-runs` | Viewer / Member | List/create queued run (`202`) |
| `GET` | `/projects/{project_id}/analysis-runs/{run_id}` | Viewer | Run status/counts |
| `POST` | `/projects/{project_id}/analysis-runs/{run_id}/cancel` | Member | Request cancellation (`202`) |
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

### Implemented: registration (Phase 2, Milestone 1)

`POST /api/v1/auth/register` takes exactly these JSON fields:

```json
{
  "email": "person@example.com",
  "password": "a long unique passphrase",
  "display_name": "Person"
}
```

Email is validated, trimmed and lowercased, with a maximum normalized length of 254.
Addresses are case insensitive; aliases such as `+tag` and dots are not rewritten.
Passwords are 12–128 characters, are not trimmed, and use Argon2id. Display names are
trimmed, nonblank, 1–100 characters, with no ASCII control characters. Unknown fields
are rejected. Email syntax validation does not verify mailbox ownership or deliverability.

`201` returns only `id`, `email`, `display_name`, `is_active`, `created_at`, and `updated_at`.
It does not log the user in, create a session, set cookies, or return tokens. Registration
and `user.registered` audit insertion commit together.

| Status | Code | Meaning |
| --- | --- | --- |
| 409 | `registration_conflict` | Registration could not be completed (duplicate normalized email) |
| 422 | `validation_error` | Invalid fields; safe locations/types only, no raw input/context |
| 429 | `rate_limited` | Registration budget exhausted; `Retry-After` gives seconds |
| 500 | `internal_error` | Unexpected failure; safe response with request ID |

The duplicate response has generic wording but its status distinguishes existing emails;
it is not enumeration-proof. Full indistinguishable registration would need a mailbox
verification flow. Login will use generic invalid-credential responses in Milestone 2.

Registration allows five attempts per client address per 3,600-second window by default.
Counters are PostgreSQL-backed and survive worker restarts. Valid JSON requests consume
the budget before field validation or hashing; rejected and duplicate requests also count.
Malformed JSON is rejected by FastAPI before dependencies. Expired counters are removed
on subsequent attempts. Rate-limit failure is closed if PostgreSQL is unavailable.
Configure with `REGISTRATION_RATE_LIMIT` and `REGISTRATION_RATE_WINDOW_SECONDS`.

The application uses the ASGI peer address, not forwarded headers directly. For local
startup use `--no-proxy-headers`; deployments must configure only explicitly trusted proxy
addresses at the server layer. SHA-256 client-address digests are transient rate-limit
keys, not an anonymization guarantee.

`X-Request-ID` accepts 1–128 ASCII letters, digits, periods, underscores, or hyphens;
invalid values are replaced with a generated UUID. Neither validation nor unexpected
error responses/logs include request bodies, SQL parameter values, or exception messages.

### Planned project and analysis behavior

Roles are Owner, Admin, Member and Viewer. Minimum roles in the table follow the matrix
in `ARCHITECTURE.md`; Admin membership operations are restricted to Member/Viewer, while
only the Owner manages Admins. Nonmembers will receive resource-safe denial responses.

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
