# DevTrace

DevTrace is an open-source codebase intelligence platform. It will help developers
understand unfamiliar repositories through static source analysis, dependency mapping,
architecture exploration, execution-flow modeling, and grounded AI explanations.

This repository currently implements **Phase 1: Foundation and local development** only.
It includes a React shell, a FastAPI service, PostgreSQL/Alembic wiring, Docker Compose,
and automated test setup. Authentication, repository ingestion, analysis, graphs, and AI
features are intentionally not present yet.

## Technology stack

- Frontend: React, TypeScript, Vite, Tailwind CSS, React Router, Axios, Lucide React
- Backend: Python 3.11+, FastAPI, Pydantic, SQLAlchemy 2.x, Alembic
- Database: PostgreSQL 15+ (Docker uses PostgreSQL 16)
- Tests: Vitest/React Testing Library and Pytest
- Local orchestration: Docker Compose

## Prerequisites

- Node.js 20+ and npm
- Python 3.11+
- Docker Desktop with Docker Compose (recommended for PostgreSQL and full-stack startup)

## Environment configuration

Copy the example before using Docker Compose or local database-backed commands:

```powershell
Copy-Item .env.example .env
```

Change `POSTGRES_PASSWORD` and update `DATABASE_URL` to the same password. `.env` is
ignored by Git and must never contain a production secret committed to the repository.

## Docker startup

```powershell
docker compose up --build
```

Open the frontend at `http://localhost:5173`, API docs at `http://localhost:8000/docs`,
and health endpoints at `http://localhost:8000/health` and `http://localhost:8000/ready`.
Run migrations in the backend service after startup:

```powershell
docker compose exec backend alembic upgrade head
```

Stop services while retaining database data:

```powershell
docker compose down
```

To also remove the local database volume (destructive):

```powershell
docker compose down --volumes
```

## Local development

Backend (PowerShell):

```powershell
py -3.11 -m venv backend/.venv
backend/.venv/Scripts/Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e "./backend[dev]"
Copy-Item .env.example .env
alembic -c backend/alembic.ini upgrade head
uvicorn app.main:app --app-dir backend --reload
```

Frontend (a second terminal):

```powershell
Set-Location frontend
npm install
npm run dev
```

For local development, start PostgreSQL with `docker compose up db -d` first. If the API
runs outside Docker, `DATABASE_URL` in `.env` must use `localhost`, as shown in the example.

## Testing

Backend tests do not require a running PostgreSQL instance because connection outcomes are
isolated at the database boundary:

```powershell
backend/.venv/Scripts/python.exe -m pytest backend/tests
```

Frontend tests:

```powershell
Set-Location frontend
npm run test -- --run
```

## Phase boundary

Follow [DEVELOPMENT_ROADMAP.md](DEVELOPMENT_ROADMAP.md) and
[DEVELOPMENT_STATUS.md](DEVELOPMENT_STATUS.md). Do not add Phase 2 authentication or any
analysis, graph, repository scanning, or AI functionality while working on Phase 1.
