# DevTrace

DevTrace is an open-source codebase intelligence platform for understanding repositories
through static analysis, dependency mapping, architecture exploration and grounded AI.

Phase 1 is complete. **Phase 2, Milestone 1: registration foundation** is implemented.
The API supports account registration with Argon2id, normalized unique emails, audit events
and shared rate limits. Login, JWT/refresh sessions, projects, RBAC and authentication UI
are scheduled in the remaining Phase 2 milestones. Analysis and AI remain deferred.

## Stack and prerequisites

- Backend: Python 3.11+, FastAPI, Pydantic, SQLAlchemy 2.x, Alembic
- Frontend: Node.js 20+, React, TypeScript, Vite, Tailwind, React Router, Axios
- Database: locally installed PostgreSQL 15+ (verified with PostgreSQL 18)
- Tests: Pytest and Vitest/React Testing Library

Use local PostgreSQL for this phase. Docker is not required or used. Historical container
files remain from Phase 1.

## Local database setup

Start your installed PostgreSQL service. On Windows its name depends on your installation
(for example, `postgresql-x64-18`). Use Services or an elevated terminal if required.
Ensure PostgreSQL's `bin` directory is on PATH before running the following commands.

Create a development login interactively; choose a local password when prompted:

```powershell
createuser -h localhost -U postgres --pwprompt devtrace
createdb -h localhost -U postgres --owner=devtrace devtrace
createdb -h localhost -U postgres --owner=devtrace devtrace_test
```

Do not recreate these objects if they already exist. `devtrace_test` is a separate database
for tests; never point tests at your development or production database.

From the repository root, create `.env` only if missing:

```powershell
if (!(Test-Path .env)) { Copy-Item .env.example .env }
```

Edit `DATABASE_URL` in `.env` to match your local credentials, using the
`postgresql+psycopg://` scheme and `localhost`. Percent-encode special characters in the
URL password. Do not commit `.env`. `POSTGRES_*` variables describe the local setup but do
not create a database automatically. Registration limits default to five attempts per
client address per hour and can be configured in `.env`.

## Backend setup and startup

From the repository root, using a standalone Python installation:

```powershell
py -3 -m venv backend/.venv
backend/.venv/Scripts/python.exe -m pip install -e "./backend[dev]"
backend/.venv/Scripts/python.exe -m alembic -c backend/alembic.ini upgrade head
backend/.venv/Scripts/python.exe -m uvicorn app.main:app --app-dir backend --reload --no-proxy-headers
```

Open API docs at `http://localhost:8000/docs`. Check liveness/readiness:

```powershell
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod http://localhost:8000/ready
```

Migrations create users, audit events and authentication rate-limit tables. The application
never calls ORM `create_all`. `--no-proxy-headers` keeps local rate limits tied to the real
peer address; configure explicit trusted proxies if deploying behind a proxy.

## Try registration

```powershell
$body = @{
  email = 'person@example.com'
  password = 'replace with a unique passphrase'
  display_name = 'Person'
} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/auth/register -ContentType 'application/json' -Body $body
```

The first request returns HTTP 201 and public user fields. Repeating the email returns
409. Invalid fields return 422. Attempts beyond the configured budget return 429 with
`Retry-After`. Registration does not start a session or issue tokens yet.

## Frontend

In a second terminal:

```powershell
Set-Location frontend
npm ci
npm run dev
```

Open `http://localhost:5173`. Milestone 1 preserves the existing frontend shell; registration
and login pages will arrive together with complete browser authentication in Milestone 4.

## Tests and migration checks

Backend unit/system tests without PostgreSQL:

```powershell
backend/.venv/Scripts/python.exe -m pytest backend/tests -m "not postgres"
```

Complete backend suite, including real PostgreSQL registration and migration tests:

```powershell
$env:TEST_DATABASE_URL = 'postgresql+psycopg://devtrace:YOUR_URL_ENCODED_PASSWORD@localhost:5432/devtrace_test'
backend/.venv/Scripts/python.exe -m pytest backend/tests -ra
backend/.venv/Scripts/python.exe -m alembic -c backend/alembic.ini check
```

`TEST_DATABASE_URL` must be set in the shell, not just `.env`. It must name a local database
ending in `_test`, owned by the test login so it can create schemas. Tests create/migrate a
random schema per test and remove only that schema. They do not drop the database or touch
its public schema. PostgreSQL tests explicitly skip if the variable is absent; such a run
is not full milestone verification. A configured but unavailable database fails the tests.
`alembic check` uses the normal `DATABASE_URL` and should follow `upgrade head`.

Frontend tests and TypeScript/production build:

```powershell
Set-Location frontend
npm run test -- --run
npm run build
```

## Delivery status

See [DEVELOPMENT_STATUS.md](DEVELOPMENT_STATUS.md) for executed verification and
[docs/PHASE_2_MILESTONES.md](docs/PHASE_2_MILESTONES.md) for milestones, implementation
decisions and the file guide. API and schema details are in [API_DESIGN.md](API_DESIGN.md)
and [DATABASE_DESIGN.md](DATABASE_DESIGN.md).

Work stops after Milestone 1 for user verification. Phase 2 is not complete until token
rotation/revocation, the authorization matrix, cross-project denial and browser flows
are implemented and tested. Do not start Phase 3.
