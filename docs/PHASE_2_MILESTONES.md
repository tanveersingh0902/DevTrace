# Phase 2 delivery milestones

Implement one milestone at a time. Stop for user verification after each. Phase 3 is
out of scope. Preserve the modular monolith and use local PostgreSQL and Alembic.

| Milestone | Deliverables | Verification gate |
| --- | --- | --- |
| 1. Registration foundation | Users, Argon2id, normalized unique email, registration API, registration audit, PostgreSQL rate limits | Registration/duplicate/input tests; real database constraints, concurrent requests, audit rollback, rate limiting, secret handling and migration round trip |
| 2. Authentication sessions | Login, short-lived JWT access, hashed opaque refresh tokens, rotation, reuse detection, expiry, revocation/logout, current-user dependencies, login/logout audit | Valid/invalid credentials, expired/wrong-signature/wrong-type tokens, concurrent refresh, replay and session revocation tests |
| 3. Project access | Project CRUD and ownership; Owner/Admin/Member/Viewer membership permissions; project/membership audit | CRUD, full role/action matrix, ownership invariants and cross-project denial tests |
| 4. Browser flows and phase exit | Register/login pages, auth context, protected routes, memory-only access tokens, refresh serialization, project list/create UI, logout | Component/integration tests for auth and project flows; complete backend/frontend suite and Phase 2 exit checklist |

## Important implementation decisions

- Routes handle HTTP, Pydantic schemas describe inputs/outputs, services own transactions
  and use cases, repositories own persistence, and SQLAlchemy models own table metadata.
- Registration returns a public user, without logging in. Session creation belongs to
  Milestone 2. No partial JWT scheme or pretend frontend authentication is introduced.
- PostgreSQL owns email uniqueness, including concurrent insertion. The API normalizes
  addresses before insertion. Duplicate responses are generic but still distinguishable
  by status; this limitation is documented in `API_DESIGN.md`.
- Argon2id uses the explicit RFC 9106 low-memory profile through `argon2-cffi`:
  [official API reference](https://argon2-cffi.readthedocs.io/en/stable/api.html).
- Audit insertion shares the user transaction. The audit schema has no free-form
  sensitive payload; project audit columns will be added with a later migration.
- A small PostgreSQL table provides atomic shared rate limiting without adding Redis
  or a process-local budget that resets whenever workers restart.
- Public errors omit Pydantic input/context and arbitrary exception text. Unexpected
  exceptions are handled before ASGI middleware can re-raise them into server logs.
  Logs retain the error class and request ID. SQLAlchemy hides bound parameters.
- The requested Owner/Admin/Member/Viewer roles supersede the original Editor design.
  Their planned permissions are in `ARCHITECTURE.md`; Milestone 1 does not implement RBAC.

## Milestone 1 file guide

| File(s) | Responsibility |
| --- | --- |
| `backend/app/models/user.py` | User fields, UUID identity and database constraints |
| `backend/app/models/audit_event.py` | Minimal security audit record and indexes |
| `backend/app/models/auth_rate_limit.py` | Shared rate-limit buckets and expiry index |
| `backend/app/models/__init__.py` | Register ORM metadata for Alembic |
| `backend/app/schemas/auth.py`, `schemas/__init__.py` | Validated registration contract, secret password representation and public user output |
| `backend/app/core/passwords.py` | Explicit Argon2id hashing and safe password verification |
| `backend/app/core/errors.py` | Safe application errors with codes and headers |
| `backend/app/repositories/users.py` | Insert/flush user without owning the transaction |
| `backend/app/repositories/audit_events.py` | Append registration audit without sensitive details |
| `backend/app/repositories/auth_rate_limits.py` | Atomic PostgreSQL budget upsert and expiration cleanup |
| `backend/app/services/registration.py` | Hash password, atomically create user/audit, map only email uniqueness violations |
| `backend/app/services/auth_rate_limits.py` | Commit attempts independently and reject over-budget requests |
| `backend/app/api/v1/auth.py`, `router.py` | Registration route, rate-limit dependency and route mounting |
| `backend/app/core/config.py` | Validated rate-limit settings |
| `backend/app/core/database.py` | Hide SQL bound parameters in diagnostic output |
| `backend/app/main.py` | Request ID bounds, safe validation/unexpected errors, application errors and retry headers |
| `backend/alembic/versions/20261117_0002_registration.py` | Reversible three-table migration |
| `backend/alembic/env.py`, `backend/alembic.ini` | Discover models, support isolated migration test connections, escape URL percent signs, resolve paths relative to config |
| `backend/tests/conftest.py` | Dedicated PostgreSQL/schema isolation and API session fixtures |
| `backend/tests/test_passwords.py` | Argon2id/salts, password verification/policy, email normalization and secret representation |
| `backend/tests/test_registration.py` | Registration, validation, duplicate races, audit rollback, rate-limit concurrency and migration coverage |
| `backend/pyproject.toml` | Argon2/email validation dependencies and PostgreSQL test marker |
| `.env.example`, `.gitignore` | Registration settings and ignored local verification tools/data |
| Root design/status/README files and this guide | Milestone scope, role design, schema/API contracts and non-Docker run/test instructions |

## Full Phase 2 exit checklist (not yet satisfied)

- [ ] Login and JWT claims/signature/type/expiry validation tested.
- [ ] Refresh rotation, concurrent refresh, replay detection and revocation tested.
- [ ] Project CRUD and Owner/Admin/Member/Viewer permission matrix tested.
- [ ] Cross-project access denied at backend boundaries.
- [ ] Required authentication/project/membership audit events tested.
- [ ] Browser register/login/protected routes/dashboard/create/logout flows tested.
- [ ] All scoped backend and frontend tests pass, with PostgreSQL tests enabled.
- [ ] User has verified each milestone and final status accurately reflects completion.
