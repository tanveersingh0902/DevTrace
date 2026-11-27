# DevTrace

[![CI on main](https://github.com/tanveersingh0902/DevTrace/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/tanveersingh0902/DevTrace/actions/workflows/ci.yml)
[![License MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

DevTrace is an open-source project for understanding how a codebase fits together. Its vision is a navigable map of files, symbols, and dependencies, with AI explanations that cite a specific repository revision.

## The problem

Tracing a request through an unfamiliar repository often means following imports by hand and checking whether an architecture diagram still matches the code. DevTrace aims to let a developer follow those relationships back to the source lines that support them.

## What works today

- A React dashboard shell with routing, reusable components, and an empty project state.
- A FastAPI service with liveness (`/health`), PostgreSQL readiness (`/ready`), version metadata (`/api/v1`), request IDs, and structured errors.
- Account registration at `POST /api/v1/auth/register`. It normalizes email addresses, enforces uniqueness in PostgreSQL, hashes passwords with Argon2id, and commits the account and audit event together. PostgreSQL also stores the per-client registration limit.
- Alembic migrations and PostgreSQL integration tests for registration, concurrency, audit rollback, rate limiting, and migration round trips.

## Planned features and roadmap

Phase 0, Phase 1, and Phase 2 Milestone 1 are implemented. **Authentication and Sessions** is next. Later Phase 2 milestones cover project access, roles, and browser authentication. Repository intake, static analysis, graph exploration, and grounded AI are planned in subsequent phases. [Public roadmap](ROADMAP.md) · [Verification history](DEVELOPMENT_STATUS.md)

## Stack and architecture

| Layer | Current implementation |
| --- | --- |
| Browser | React, TypeScript, React Router, Vite, Tailwind CSS, Axios |
| API | Python, FastAPI, Pydantic Settings, Argon2id |
| Persistence | PostgreSQL, SQLAlchemy 2, psycopg 3, Alembic |
| Verification | pytest, Vitest, React Testing Library, TypeScript compiler |

The backend is a modular monolith. The diagram shows the implemented registration path. Registration is currently available through the API. The browser's dashboard is a separate entry point.

```mermaid
flowchart LR
    Browser["Browser"] --> UI["React dashboard"]
    Client["API client"] --> Route["FastAPI registration route"]
    Route --> Limit["Rate limit service"]
    Route --> Register["Registration service"]
    Limit --> Repo["Repositories"]
    Register --> Repo
    Repo --> DB[("PostgreSQL")]
```

The design documents describe the intended worker, graph, and AI boundaries as well as the current API and schema. [Architecture](ARCHITECTURE.md) · [API design](API_DESIGN.md) · [Database design](DATABASE_DESIGN.md)

## Repository structure

```text
.github/             Issue forms, pull request template, and CI
backend/
  app/               API routes, services, repositories, models, and settings
  alembic/           Migration environment and versioned revisions
  tests/             Unit, API, PostgreSQL, and migration tests
  pyproject.toml     Python runtime and development dependencies
frontend/
  src/               React app, dashboard, components, API client, and tests
  package-lock.json  npm dependency lockfile
docs/                Phase 2 milestones, implementation guide, and exit criteria
```

## Local development on Windows

Install Git, a standalone Python 3.11+ with the Windows launcher, Node.js 20+ with npm, and a local PostgreSQL 15+ server with its command-line tools on `PATH`. Run the examples in PowerShell. Start in the repository root unless a command changes directory.

```powershell
git clone https://github.com/tanveersingh0902/DevTrace.git
Set-Location DevTrace
py -3 -m venv backend/.venv
.\backend\.venv\Scripts\python.exe -m pip install -e "./backend[dev]"
```

### PostgreSQL and environment variables

Start your installed PostgreSQL service using Windows Services. For a new setup, run the commands below as the PostgreSQL administrator and choose a local password for the `devtrace` login. Reuse the role and databases if you already created them.

```powershell
createuser -h localhost -U postgres --pwprompt devtrace
createdb -h localhost -U postgres --owner=devtrace devtrace
createdb -h localhost -U postgres --owner=devtrace devtrace_test
if (!(Test-Path .env)) { Copy-Item .env.example .env }
```

Edit the root `.env` before starting the API. Use a URL-encoded password in the database URL. [Configuration example](.env.example)

| Setting | Purpose |
| --- | --- |
| `DATABASE_URL` | API and Alembic connection, e.g. `postgresql+psycopg://devtrace:YOUR_ENCODED_PASSWORD@localhost:5432/devtrace` |
| `TEST_DATABASE_URL` | Shell variable used by pytest. Use a separate local database ending in `_test` whose owner can create schemas. |
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_PORT` | Describe local database settings. Set up the server and login using PostgreSQL tools and keep `DATABASE_URL` in sync. |
| `APP_ENV`, `APP_NAME`, `API_V1_PREFIX`, `LOG_LEVEL` | Application environment, title, versioned route prefix, and log level |
| `CORS_ORIGINS` | Comma-separated browser origins, default `http://localhost:5173` |
| `DATABASE_POOL_SIZE`, `DATABASE_MAX_OVERFLOW` | SQLAlchemy pool capacity and additional connections, default 5 and 10 |
| `REGISTRATION_RATE_LIMIT`, `REGISTRATION_RATE_WINDOW_SECONDS` | Registration attempts per client and window, default 5 per 3,600 seconds |
| `VITE_API_BASE_URL` | Public API origin compiled into the frontend, default `http://localhost:8000`. Set in the frontend shell or `frontend/.env.local` before starting or building Vite. |

### Migrate and start the backend

```powershell
$python = '.\backend\.venv\Scripts\python.exe'
& $python -m alembic -c backend/alembic.ini upgrade head
& $python -m alembic -c backend/alembic.ini current
& $python -m uvicorn app.main:app --app-dir backend --reload --no-proxy-headers
```

Alembic creates the users, audit events, and rate-limit tables. The local startup command uses the peer address for rate limiting. In a second PowerShell window, open `http://localhost:8000/docs` or check the running API.

```powershell
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod http://localhost:8000/ready
```

To try registration, submit an example account to the local API.

```powershell
$body = @{
  email = 'person@example.com'
  password = 'example passphrase for local testing'
  display_name = 'Person'
} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/auth/register -ContentType 'application/json' -Body $body
```

A successful request returns HTTP 201 with public user fields. Duplicate emails return 409, invalid fields return 422, and exhausted rate limits return 429 with `Retry-After`.

### Start the frontend

From the repository root in a separate terminal, run the following commands and open `http://localhost:5173`.

```powershell
Set-Location frontend
npm.cmd ci
npm.cmd run dev
```

## Verification

From the root, set the test URL **in the shell** and replace the password placeholder. Each PostgreSQL test migrates a randomly named schema and removes it after the test. Use a dedicated test database.

```powershell
$python = '.\backend\.venv\Scripts\python.exe'
$env:TEST_DATABASE_URL = 'postgresql+psycopg://devtrace:YOUR_ENCODED_PASSWORD@localhost:5432/devtrace_test'
& $python -m pytest backend/tests -ra
& $python -m alembic -c backend/alembic.ini check
```

The drift check uses `DATABASE_URL` and requires the development database to be at the migration head. For a quick run without PostgreSQL, use `& $python -m pytest backend/tests -m "not postgres"`. The full suite skips database cases if the test URL is absent.

After installing the frontend dependencies, run the checks from `frontend`.

```powershell
npm.cmd exec -- tsc -b
npm.cmd run test -- --run
npm.cmd run build
```

CI runs both jobs on pushes and pull requests targeting `main`. The project currently has no dedicated lint or format commands. [CI workflow](.github/workflows/ci.yml)

## Contributing

Use the issue forms for bugs and proposals. The contributor guide covers branch setup, tests, and pull request review. [Contributing](CONTRIBUTING.md) · [Code of conduct](CODE_OF_CONDUCT.md) · [Changelog](CHANGELOG.md)

## Security

Report suspected vulnerabilities privately and redact sensitive data from examples. [Security policy](SECURITY.md)

## License

Copyright (c) 2026 Tanveer Singh. DevTrace is distributed under the [MIT License](LICENSE).
