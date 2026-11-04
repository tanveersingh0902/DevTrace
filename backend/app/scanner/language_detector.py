"""Extension-based language detection for repository files."""

from pathlib import Path

_LANGUAGE_BY_EXTENSION = {
    ".py": "Python",
    ".java": "Java",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".mts": "TypeScript",
    ".cts": "TypeScript",
    ".md": "Markdown",
    ".markdown": "Markdown",
    ".json": "JSON",
    ".html": "HTML",
    ".htm": "HTML",
    ".css": "CSS",
    ".c": "C",
    ".h": "C",
    ".cc": "C++",
    ".cpp": "C++",
    ".cxx": "C++",
    ".hh": "C++",
    ".hpp": "C++",
    ".hxx": "C++",
    ".go": "Go",
    ".rs": "Rust",
    ".sql": "SQL",
    ".sh": "Shell",
    ".bash": "Shell",
    ".zsh": "Shell",
}


def detect_language(path: Path) -> str:
    """Return a language name based only on the file extension."""
    return _LANGUAGE_BY_EXTENSION.get(path.suffix.lower(), "Unknown")
