# DevTrace

**Understand Any Codebase. Trace Every Connection.**

DevTrace is an open-source Codebase Intelligence and Visualisation Platform that helps developers understand unfamiliar software repositories through automated analysis and interactive dependency graphs.

## What DevTrace Does

- **Scans repositories** to discover files, functions, and classes
- **Detects dependencies** between files, functions, and modules
- **Generates interactive graphs** showing how code is connected
- **Identifies architectural patterns** and potential issues
- **Helps onboarding** when joining an existing project

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python, FastAPI |
| Code Parsing | Tree-sitter |
| Graph Analysis | NetworkX |
| Database | SQLite |
| Frontend | React, TypeScript, Tailwind CSS |
| Visualisation | React Flow |

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Git

### Backend Setup

```bash
cd backend
python -m venv .venv

# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

pip install -e ".[dev]"
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000` with interactive docs at `http://localhost:8000/docs`.

### Run Tests

```bash
cd backend
pytest -v
```

## Project Status

DevTrace is under active development.

- [x] Project structure and configuration
- [ ] Repository scanner
- [ ] Code parser (Tree-sitter)
- [ ] Dependency analysis
- [ ] Graph generation
- [ ] API endpoints
- [ ] React frontend
- [ ] Interactive visualisation

## Supported Languages

| Language | Status |
|----------|--------|
| Python | 🔜 In Progress |
| JavaScript | 🔜 Planned |
| TypeScript | 🔜 Planned |
| Java | 🔜 Planned |

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting a pull request.

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

## Security

To report a security vulnerability, please see [SECURITY.md](SECURITY.md).

