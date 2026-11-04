"""Default exclusions and practical, common .gitignore pattern support."""

import stat
from dataclasses import dataclass
from fnmatch import fnmatchcase
from pathlib import Path

IGNORED_DIRECTORIES = frozenset(
    {
        ".git",
        ".venv",
        "venv",
        "node_modules",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".cache",
        ".tox",
        ".nox",
        "dist",
        "build",
        "coverage",
        "htmlcov",
        "target",
        ".next",
        ".idea",
        ".vscode",
    }
)

_IGNORED_EXTENSIONS = frozenset(
    {
        ".pyc",
        ".pyo",
        ".class",
        ".o",
        ".a",
        ".obj",
        ".lib",
        ".dll",
        ".so",
        ".dylib",
        ".exe",
        ".pyd",
        ".jar",
        ".war",
        ".ear",
        ".wasm",
        ".pdb",
        ".cache",
        ".pid",
        ".swp",
        ".swo",
        ".tmp",
        ".temp",
        ".bak",
        ".orig",
        ".rej",
    }
)
_IGNORED_FILES = frozenset({".ds_store", "thumbs.db", "desktop.ini", ".coverage"})
_MAX_GITIGNORE_BYTES = 1_000_000


@dataclass(frozen=True)
class GitIgnoreRule:
    """A single .gitignore rule scoped to the directory containing it."""

    base_directory: Path
    pattern: str
    negated: bool
    directory_only: bool
    has_slash: bool

    def matches(self, relative_path: Path, is_directory: bool) -> bool:
        """Check whether this rule applies to a repository-relative path."""
        try:
            scoped_path = relative_path.relative_to(self.base_directory).as_posix()
        except ValueError:
            return False

        if self.directory_only and not is_directory:
            return False
        if self.has_slash:
            return fnmatchcase(scoped_path, self.pattern)
        return fnmatchcase(Path(scoped_path).name, self.pattern)


def is_ignored_name(name: str, is_directory: bool) -> bool:
    """Check built-in directory, compiled-file, cache, and temporary rules."""
    if is_directory:
        return name.lower() in IGNORED_DIRECTORIES
    if name.lower() in _IGNORED_FILES:
        return True
    suffix = Path(name).suffix.lower()
    return (
        suffix in _IGNORED_EXTENSIONS
        or name.endswith("~")
        or (name.startswith("#") and name.endswith("#"))
    )


def load_gitignore_rules(directory: Path, relative_directory: Path) -> list[GitIgnoreRule]:
    """Read a bounded, regular .gitignore file without following symlinks."""
    gitignore = directory / ".gitignore"
    try:
        metadata = gitignore.lstat()
    except FileNotFoundError:
        return []
    except PermissionError as error:
        raise PermissionError("Unable to read repository ignore rules.") from error

    if not stat.S_ISREG(metadata.st_mode):
        return []

    try:
        with gitignore.open("rb") as ignore_file:
            content = ignore_file.read(_MAX_GITIGNORE_BYTES + 1)
    except PermissionError as error:
        raise PermissionError("Unable to read repository ignore rules.") from error
    if len(content) > _MAX_GITIGNORE_BYTES:
        raise ValueError("A .gitignore file exceeds the supported size.")

    rules: list[GitIgnoreRule] = []
    for line in content.decode("utf-8", errors="replace").splitlines():
        pattern = line.strip()
        if not pattern or (pattern.startswith("#") and not pattern.startswith(r"\#")):
            continue

        negated = pattern.startswith("!") and not pattern.startswith(r"\!")
        if negated or pattern.startswith((r"\#", r"\!")):
            pattern = pattern[1:]

        pattern = pattern.rstrip("/")
        if not pattern or pattern == ".":
            continue
        has_slash = "/" in pattern.lstrip("/")
        rules.append(
            GitIgnoreRule(
                base_directory=relative_directory,
                pattern=pattern.lstrip("/"),
                negated=negated,
                directory_only=line.rstrip().endswith("/"),
                has_slash=has_slash or pattern.startswith("/"),
            )
        )
    return rules


def is_ignored_by_gitignore(
    relative_path: Path,
    is_directory: bool,
    rules: list[GitIgnoreRule],
) -> bool:
    """Apply ordered .gitignore rules; the last matching rule takes precedence."""
    ignored = False
    for rule in rules:
        if rule.matches(relative_path, is_directory):
            ignored = not rule.negated
    return ignored
