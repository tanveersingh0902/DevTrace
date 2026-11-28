# DevTrace roadmap

DevTrace supports registration and authenticated API sessions. Phase 2 Milestone 2 awaits manual verification before project access work begins. The sequence below describes scope without promising release dates.

| Phase | Status | Outcome |
| --- | --- | --- |
| 0 · Architecture | Complete | System boundaries, API design, data model, and phased delivery plan |
| 1 · Foundation | Complete | React shell, FastAPI probes and metadata, PostgreSQL migrations, and test harnesses |
| 2 · Identity and project access | In progress | M1 registration and M2 login, rotation, and revocation implemented. M3 adds project access and roles. M4 adds browser flows and phase exit checks. |
| 3 · Repository intake | Planned | Repository source registration, durable jobs, and worker recovery |
| 4 · Structural analysis | Planned | File and symbol extraction for a first supported language |
| 5 · Dependency graph | Planned | Persisted graph and bounded explorer API |
| 6 · Architecture explorer | Planned | Interactive graph navigation, filters, and source details |
| 7 · Execution flows | Planned | Static call and route-to-handler relationships with evidence |
| 8 · Grounded AI | Planned | Snapshot-scoped explanations with source citations |
| 9 · Operations and expansion | Planned | Recovery, observability, hardening, and additional languages |

OS-1 adds the repository's open-source foundation alongside Phase 2. For verification results, see [development status](DEVELOPMENT_STATUS.md). The engineering plan owns the detailed scope and exit criteria. [Development roadmap](DEVELOPMENT_ROADMAP.md) · [Phase 2 milestones](docs/PHASE_2_MILESTONES.md)
