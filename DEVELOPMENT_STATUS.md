# Development Status

Updated November 27, 2026. Phase OS-1 establishes the open-source repository foundation on
`chore/open-source-foundation`. Phase 2 remains in progress. Registration is implemented.
The next milestone, **Phase 2 Milestone 2 — Authentication and Sessions**, awaits manual approval.

## Phase OS-1 — Repository foundation

The audit found a React dashboard shell, a FastAPI modular monolith, two Alembic revisions,
and PostgreSQL registration integration tests. The backend declares Python 3.11+ and uses
pip with the `dev` extra. The frontend uses npm with a committed cross-platform lockfile.
The project documents Node.js 20+ and PostgreSQL 15+. Neither stack defines a lint or
format command. Package versions in the manifests describe the software under development.
The changelog tracks this work under Unreleased.

| Files | OS-1 change |
| --- | --- |
| `LICENSE`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md` | Added the MIT license, contribution workflow, Contributor Covenant adoption, and private reporting instructions. |
| `ROADMAP.md`, `CHANGELOG.md` | Added a public milestone overview linked to the existing detailed engineering roadmap and an Unreleased change history. |
| `.github/ISSUE_TEMPLATE/bug_report.yml`, `.github/ISSUE_TEMPLATE/feature_request.yml`, `.github/ISSUE_TEMPLATE/config.yml`, `.github/PULL_REQUEST_TEMPLATE.md` | Added issue forms, a security-policy link in the issue chooser, and review prompts. |
| `.github/workflows/ci.yml` | Added independent Backend and Frontend checks on main pushes and PRs into main. CI starts the runner's native PostgreSQL service, creates job-local databases and credentials, and uses read-only repository permissions. |
| `.editorconfig` | Added encoding, line ending, indentation, and final newline defaults. |
| `README.md`, `.env.example`, `.gitignore`, `DEVELOPMENT_STATUS.md` | Updated the contributor entry point, database pool and Vite environment guidance, ignore rules, and verification record. |

### OS-1 verification

Local verification used Python 3.13.14, PostgreSQL 18, Node.js 24.19.0, and npm 11.17.0.
The Python launcher found no standalone installation, so the checks used pgAdmin's bundled
Python and the existing ignored development packages. The Alembic and pytest commands below
identify the module entry points invoked with that interpreter. Both database URLs targeted
the disposable cluster on loopback port 55432. Its startup and shutdown procedure appears
in the historical environment notes below. Frontend checks used the existing installed
dependencies in `frontend`.

| Check | Local result |
| --- | --- |
| `alembic -c backend/alembic.ini upgrade head`, `current`, `check` | Head `20261117_0002`. No new upgrade operations detected. |
| `pytest backend/tests -ra` with `TEST_DATABASE_URL` | 28 passed, zero skipped. Includes migration downgrade/upgrade, drift, concurrency, and audit rollback. One upstream Starlette/HTTPX test-client deprecation warning. |
| `npm.cmd exec -- tsc -b` | Passed. |
| `npm.cmd run test -- --run` | 2 tests passed. |
| `npm.cmd run build` | TypeScript and Vite production build passed. |
| PyYAML parsing and structural checks | Parsed the workflow, both issue forms, and the chooser. Checked triggers, jobs, permissions, cache inputs, form fields and contact-link structure. |
| Markdown link and heading check | Resolved 24 local links across 14 Markdown files. Hosted workflow, badge, and security-policy presentation require verification on GitHub after adoption. |
| `git diff --check` and working-tree review | Passed. Checked whitespace and common credential signatures across all 16 changed and new files. Reviewed credential examples and CI password handling. |
| `git check-ignore` and `git ls-files` | Local environment files, virtual environments, dependencies, build output, temporary database files, and sample private-key paths are ignored. The root example environment file is tracked. |

### GitHub configuration and remaining verification

1. Review the branch and submit the changes for review. Confirm Actions is enabled and
   inspect the first hosted Backend and Frontend job results. Local checks used Windows.
2. Once the checks have run, configure the desired `main` ruleset and select **Backend**
   and **Frontend** as required checks if enforcing CI before merge.
3. Enable or confirm private vulnerability reporting in repository settings. After adoption
   on the default branch, check that the security policy, reporting button, issue chooser,
   pull request template, and CI badge render as intended.
4. Review OS-1 and explicitly approve Phase 2 Milestone 2 before beginning implementation.

## Phase 2 Milestone 1 — November 18, 2026

### Completed functionality

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

### Milestone 1 verification

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

### Milestone 1 local verification environment

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
