# Contributing to DevTrace

Start with the [roadmap](ROADMAP.md) to see which capabilities exist and which milestone owns a proposal. Bug reports should give a repeatable example and identify the commit tested. For a feature that changes a milestone or an API contract, discuss the use case before building it. For a suspected vulnerability, follow the [security policy](SECURITY.md).

## Set up a working copy

Follow the [PowerShell setup and testing guide](README.md#local-development-on-windows) to create a Python virtual environment, install the API and frontend, and migrate local PostgreSQL. Keep a separate local database ending in `_test` for the integration suite.

If you contribute from a fork, clone your fork and add the project as `upstream`. Start each change from the current upstream main branch.

```powershell
git remote add upstream https://github.com/tanveersingh0902/DevTrace.git
git fetch upstream
git switch -c docs/clarify-setup upstream/main
```

Add the remote once. Contributors working in a clone of the main repository can use `origin/main`. Choose a short branch name such as `fix/registration-error` or `docs/clarify-setup`.

## Make and test the change

Keep each pull request focused on one problem. Preserve the route, service and repository boundaries described in the [architecture](ARCHITECTURE.md). Include an Alembic migration for a schema change and update the [API contract](API_DESIGN.md) when a caller-visible contract changes.

| Change | Checks before review |
| --- | --- |
| Backend or migrations | Run the complete pytest suite with `TEST_DATABASE_URL` set. Run `alembic upgrade head` and `alembic check` using the repository config. Add coverage for changed behavior. |
| Frontend | Run the TypeScript check, Vitest in single-run mode, and the production build. Include screenshots for visible changes. |
| Documentation or CI | Check changed links, YAML and command examples. Run the jobs affected by workflow changes. |
| Every pull request | Inspect the diff for unintended files and credentials. Run `git diff --check`. Record any skipped checks and why. |

Use the [exact local commands](README.md#verification). A pytest run that skips the PostgreSQL cases covers only part of the backend.

## Commits, pull requests and review

Use Conventional Commits in the form `type(scope): short imperative summary`. Examples include `docs(setup): explain the test database` and `fix(api): preserve request IDs in errors`. A scope is optional.

Open a pull request against `main`. Fill in the template with the motivation, related issue, testing results, and any security or documentation impact. During review, explain design decisions, address comments in the same branch, and rerun checks affected by revisions. Reviewers should check behavior, test evidence and milestone scope. Follow the [code of conduct](CODE_OF_CONDUCT.md) when giving or receiving feedback.
