# Changelog

This project records notable changes using [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## Unreleased

### Added

- Login, current-user lookup, rotating refresh cookies, session revocation and replay detection backed by PostgreSQL. Migration `20261128_0003` adds refresh families and token history.

- React dashboard shell and FastAPI foundation with liveness, database readiness, and API metadata endpoints.
- PostgreSQL account registration with Argon2id passwords, registration audit events, shared rate limits, and reversible Alembic migrations.
- MIT license, community policies, contributor guide, public roadmap, issue forms, and a pull request template.
- Separate backend and frontend CI jobs covering migrations, PostgreSQL integration tests, TypeScript, frontend tests, and the production build.

### Changed

- Reworked the README around the implemented milestone and the Windows PowerShell development workflow.
- Documented database pool settings and Vite environment loading, consolidated ignore rules, and added editor defaults.
