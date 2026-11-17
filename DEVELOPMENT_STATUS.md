# Development Status

**Last updated:** 2026-11-18
**Current phase:** Phase 2 - Identity and project access
**Status:** Milestone 1 implemented and verified; awaiting user verification before Milestone 2.
**Phase 2 overall:** In progress. Exit criteria are not yet satisfied.

## Completed functionality

Phase 0 architecture and Phase 1 application foundations are preserved. This milestone adds:

- PostgreSQL users with UUID identity, normalized unique email, Argon2id password hashes,
  display names, active status and timezone-aware timestamps.
- `POST /api/v1/auth/register` with strict inputs, public user responses, race-safe duplicate
  handling and explicit UTC response timestamps.
- Atomic registration and `user.registered` audit insertion. Failure to persist the audit
  rolls back user creation.
- PostgreSQL-backed registration rate limits shared across workers and restarts, with
  expiration, independent attempt commits and `Retry-After` responses.
- Secret-safe validation errors and unexpected-error handling; bounded request IDs and
  hidden SQL bound parameters.
- Reversible Alembic migration `20261117_0002` and repository-root migration commands.
- PostgreSQL integration tests using individually migrated disposable test schemas.
- Updated API/database designs, role design, roadmap, local development instructions and
  milestone/file guide.

No Docker command was used. Existing container files were left in place. The frontend
source remains unchanged for this backend milestone.

## Verification executed

| Check | Result |
| --- | --- |
| Complete backend Pytest suite with `TEST_DATABASE_URL` set | **28 passed**, no skipped tests |
| PostgreSQL migration upgrade/downgrade/upgrade and Alembic metadata comparison | Passed as part of backend tests |
| Repository-root Alembic `upgrade head` | Passed against isolated local PostgreSQL |
| Repository-root Alembic `check` | Passed: no new upgrade operations detected |
| Actual `/health` and `/ready`, without database dependency overrides | HTTP 200 for both |
| `npm.cmd run test -- --run` in `frontend` | **2 passed** |
| `npm.cmd run build` in `frontend` | Passed: TypeScript and Vite production build |
| `git diff --check` | Passed |

Backend coverage includes password profile/salting/verification, registration, case-insensitive
email conflicts, concurrent duplicate registration, invalid fields, public response fields,
UTC timestamps, audit insertion/rollback, error/log secrecy, request ID bounds, database
constraints, rate-limit expiry/restarts/concurrency/client separation, migration drift and
round trips. Existing system tests also pass.

One upstream deprecation warning remains: the installed Starlette version deprecates its
HTTPX-backed test client. It does not affect the passing tests; migrating the test transport
can be handled separately when updating dependencies.

## Local verification environment

The machine has PostgreSQL 18 and pgAdmin's bundled Python 3.13.14, but `py -0p` reports no
standalone Python installation. Verification therefore used the bundled interpreter with
backend development dependencies installed into ignored `.local/python-deps`. No global
Python installation or pgAdmin packages were modified.

A separate temporary PostgreSQL cluster was initialized under ignored `.local/postgres-data`,
listening only on `127.0.0.1:55432`, using database/login `devtrace_test`. It uses local trust
authentication for disposable testing only. The installed PostgreSQL Windows service and
existing development database were not changed. The temporary server is stopped after
verification; its ignored data and downloaded dependencies remain available for review.

Sandbox restrictions required elevated tool execution for dependency downloads, PostgreSQL
startup and test/build execution. All required verification completed successfully.

For normal development, install standalone Python 3.11+, start your local PostgreSQL service,
and follow the complete setup and run/test commands in `README.md`.

To reproduce the backend verification on this machine using the retained temporary setup,
run the following from the repository root in a normal PowerShell terminal:

```powershell
$pgBin = 'C:\Program Files\PostgreSQL\18\bin'
$testPython = 'C:\Program Files\PostgreSQL\18\pgAdmin 4\python\python.exe'
& "$pgBin\pg_ctl.exe" -D '.local/postgres-data' -l '.local/postgres.log' -o '-h 127.0.0.1 -p 55432' -w start
$env:TEST_DATABASE_URL = 'postgresql+psycopg://devtrace_test@127.0.0.1:55432/devtrace_test'
& $testPython -c "import sys; sys.path[:0] = ['backend', '.local/python-deps']; import pytest; sys.exit(pytest.main(['backend/tests', '-ra']))"
& "$pgBin\pg_ctl.exe" -D '.local/postgres-data' -m fast -w stop
```

## Remaining milestones and verification gate

1. **Milestone 1: registration foundation** - implemented, tests passed, awaiting user verification.
2. **Milestone 2: authentication sessions** - not started. Login, JWT access tokens, refresh
   sessions/rotation/reuse detection, logout/revocation, protected dependencies, login/logout audit.
3. **Milestone 3: project access** - not started. Project CRUD/ownership, memberships,
   Owner/Admin/Member/Viewer backend enforcement, project/membership audit and denial tests.
4. **Milestone 4: browser flows and Phase 2 verification** - not started. Auth pages/context,
   protected routes, dashboard/create project/logout, component tests and full exit checks.

Implementation decisions and each important file are explained in
[docs/PHASE_2_MILESTONES.md](docs/PHASE_2_MILESTONES.md). Registration's duplicate response
uses generic wording but remains distinguishable by status; mailbox verification is not
implemented. No session is created by registration.

Work stops here for user verification. Phase 2 is not declared complete. No Phase 3 work
has started.
