# DevTrace

**Understand Any Codebase. Trace Every Connection.**

DevTrace is an open-source Codebase Intelligence and Visualisation Platform that helps developers understand unfamiliar software repositories through automated analysis and interactive dependency graphs.

## What DevTrace Does

- **Scans repositories** to inventory files, folders, languages, and file metadata
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

### Scan a Local Repository

The scanner is available at `POST /api/v1/scan`. It accepts a local filesystem path:

```json
{
  "repository_path": "/path/to/repository"
}
```

For example, from a shell:

```bash
curl -X POST http://localhost:8000/api/v1/scan \
  -H "Content-Type: application/json" \
  -d '{"repository_path": "/path/to/repository"}'
```

For safety, scans are limited to `scan_allowed_roots`, which defaults to the server's current
working directory. Set `SCAN_ALLOWED_ROOTS` in the backend environment to a JSON array of
directories when repositories live elsewhere, for example:

```text
SCAN_ALLOWED_ROOTS=["/path/to/projects"]
```

The scanner does not execute source code or read source-file contents; it reads bounded
`.gitignore` files to apply common ignore patterns. Language detection uses file extensions only,
with unrecognized extensions reported as `Unknown`. It reports file metadata and language counts,
skips symbolic links and files larger than `MAX_FILE_SIZE_BYTES`, and rejects scans exceeding
`MAX_FILES`. Common generated/dependency directories are excluded. Absolute server paths are not
included in the API response.

### Run Tests

```bash
cd backend
pytest -v
```

## Project Status

DevTrace is under active development.

- [x] Project structure and configuration
- [x] Repository scanner and scan API
- [ ] Code parser (Tree-sitter)
- [ ] Dependency analysis
- [ ] Graph generation
- [ ] Remaining analysis API endpoints
- [ ] React frontend
- [ ] Interactive visualisation

## Supported Languages

| Language | Status |
|----------|--------|
| Python | ✅ Detected |
| Java | ✅ Detected |
| JavaScript | ✅ Detected |
| TypeScript | ✅ Detected |
| Markdown | ✅ Detected |
| JSON | ✅ Detected |
| HTML | ✅ Detected |
| CSS | ✅ Detected |
| C / C++ | ✅ Detected |
| Go | ✅ Detected |
| Rust | ✅ Detected |
| SQL | ✅ Detected |
| Shell | ✅ Detected |

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting a pull request.

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

## Security

To report a security vulnerability, please see [SECURITY.md](SECURITY.md).
