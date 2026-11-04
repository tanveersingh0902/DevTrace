# Contributing to DevTrace

Thank you for your interest in contributing to DevTrace! This guide will help you get started.

## Development Setup

### Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher
- Git

### Getting Started

1. **Fork the repository** on GitHub.

2. **Clone your fork:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/DevTrace.git
   cd DevTrace
   ```

3. **Set up the backend:**
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -e ".[dev]"
   ```

4. **Set up the frontend:**
   ```bash
   cd frontend
   npm install
   ```

5. **Run the tests:**
   ```bash
   # Backend
   cd backend
   pytest

   # Frontend
   cd frontend
   npm test
   ```

## How to Contribute

### Reporting Bugs

- Use the [Bug Report](https://github.com/YOUR_USERNAME/DevTrace/issues/new?template=bug_report.md) issue template.
- Include steps to reproduce the issue.
- Include your environment details (OS, Python version, Node.js version).

### Suggesting Features

- Use the [Feature Request](https://github.com/YOUR_USERNAME/DevTrace/issues/new?template=feature_request.md) issue template.
- Explain the use case and why this feature would be valuable.

### Submitting Code

1. Create a feature branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes. Follow the coding standards below.

3. Write or update tests for your changes.

4. Run the linter:
   ```bash
   cd backend
   ruff check .
   ruff format .
   ```

5. Commit with a clear message:
   ```bash
   git commit -m "feat: add dependency cycle detection"
   ```

6. Push and open a Pull Request against `main`.

## Coding Standards

### Python (Backend)

- Follow PEP 8 conventions.
- Use type hints for all function signatures.
- Write docstrings for public functions and classes.
- Use Ruff for linting and formatting.
- Keep functions focused — one function, one responsibility.

### TypeScript (Frontend)

- Use TypeScript strict mode.
- Use functional components with hooks.
- Follow the existing component structure.

### Commit Messages

We follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` — A new feature
- `fix:` — A bug fix
- `docs:` — Documentation changes
- `test:` — Adding or updating tests
- `refactor:` — Code changes that neither fix a bug nor add a feature
- `chore:` — Maintenance tasks

### Pull Requests

- Keep PRs focused on a single change.
- Reference any related issues.
- Include a clear description of what changed and why.
- Ensure all CI checks pass.

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## Questions?

Open a [Discussion](https://github.com/YOUR_USERNAME/DevTrace/discussions) if you have questions about contributing.

