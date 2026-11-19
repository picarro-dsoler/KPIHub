"""Shared path setup for KPIHubDev/SQLite scripts."""

import os
import sys
from pathlib import Path

SQLITE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = SQLITE_ROOT.parent
WORKSPACE_ROOT = REPO_ROOT.parent


def _locallib_roots() -> list[Path]:
    roots: list[Path] = []
    seen: set[Path] = set()
    for candidate in (
        REPO_ROOT,
        WORKSPACE_ROOT / "KPIHub",
        WORKSPACE_ROOT / "KPIHubDev",
        WORKSPACE_ROOT / "locallib_packages",
    ):
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if (resolved / "locallib").is_dir():
            roots.append(resolved)
    return roots


def activate() -> Path:
    """Configure sys.path and cwd for KPIHubDev/SQLite layout."""
    path_entries = [str(SQLITE_ROOT)]
    for root in _locallib_roots():
        path_entries.append(str(root))

    sys.path[:] = path_entries + [p for p in sys.path if p not in path_entries]
    os.chdir(SQLITE_ROOT)
    (SQLITE_ROOT / "database").mkdir(parents=True, exist_ok=True)
    (SQLITE_ROOT / "logs").mkdir(parents=True, exist_ok=True)
    return SQLITE_ROOT
