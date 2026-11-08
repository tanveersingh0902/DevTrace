# DevTrace Development Roadmap

**Status:** Sequential plan. Later phases must not be implemented early.

## Delivery rules

- Complete a phase only when scoped tests pass and documentation/status are updated.
- New behavior requires unit tests; database, API, worker, provider, and UI boundaries
  require integration/component tests as applicable.
- Schema changes require Alembic migrations; API changes update `API_DESIGN.md`.
- Keep scope narrow, avoid unnecessary dependencies, and never use mock production behavior.

## Phase 0 — Architecture and planning (current)

Create the requested architecture, data, API, roadmap, and status documentation only. No
application code, database schema, dependency manifest, container setup, or test framework
is introduced.

## Phase 1 — Foundation and local development

Create React/TypeScript/Vite/Tailwind shell; FastAPI app; configuration, errors and
health/readiness endpoints; SQLAlchemy/Alembic/PostgreSQL foundation; Docker Compose;
Pytest/Vitest; and documented lint/type/test commands.

Exit: clean checkout starts locally; health/database migration integration tests and
frontend route/component tests pass. No authentication, repository processing, analysis,
or AI is included.

## Phase 2 — Identity and project access

Implement users, refresh sessions, projects/memberships; Argon2id/JWT/rotating-refresh
authentication; resource-level roles; audit events; login/register/protected routes and
project list/create UI; and rate limits.

Exit: token rotation, revocation, authorization matrix, and cross-project denial tested.

## Phase 3 — Repository registration and durable jobs

Implement safe repository-source metadata/validation, analysis-run/job state, idempotent
job creation, worker lease/recovery/cancellation, status UI, and static-content guardrails.
Choose one safe source mode end-to-end (recommended: validated public Git URL or upload
archive). Private repository credentials remain deferred.

Exit: state transitions, idempotency, lease recovery, authorization, and unsafe URL/path
rejection are tested; workers never execute repository code.

## Phase 4 — First-language structural analysis

Choose one initial language (TypeScript/JavaScript recommended), then add Tree-sitter
adapter, discovery/limits, parser diagnostics, file/module/symbol extractors, provenance,
and fixture repositories.

Exit: immutable completed runs store structural output; malformed, ignored, unsupported,
and expected fixture extraction behavior is tested.

## Phase 5 — Dependency graph and explorer API

Add NetworkX multigraph construction, resolution, validation, metrics, graph persistence,
and bounded graph/file/symbol/detail/summary APIs.

Exit: expected fixture graph, direction/multiplicity/confidence, traversal caps, and
authorization are tested.

## Phase 6 — Interactive architecture explorer

Implement run navigation/status, React Flow graph, filters/search, detail panel,
source-location display, and loading/empty/error states.

Exit: Vitest covers primary exploration flows and browser graph limits remain enforced.

## Phase 7 — Static execution flows

Add supported static call relationships, entry points, and routing-to-handler discovery.
Label all flow as inference, not observed runtime behavior.

Exit: recursion/cycles, confidence, semantics, and fixture results are tested.

## Phase 8 — Grounded AI explanations

Implement provider-neutral interface and one provider adapter first; then context bounds,
redaction, citations, conversations, usage/audit records, failures, and UI. Add other
providers only after the first adapter contract is proven.

Exit: provider contract, authorization, context-cap, citation, failure, and secret
non-disclosure tests pass; AI cannot mutate analysis.

## Phase 9 — Operations, hardening, and language expansion

Add observability, backups/recovery runbook, security review, dependency scanning,
performance/load testing, measured worker scaling, retention controls, deployment guidance,
and additional language extractors one at a time.

## Deferred by design

Microservices, graph/vector databases, cache clusters, queue brokers, private-repository
OAuth, SSO/SCIM, public sharing, runtime instrumentation, and code-writing agents.
