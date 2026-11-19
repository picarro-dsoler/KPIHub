"""sys.path + env so dashboard can import KPIHub Python (lib.*, locallib)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

_DASHBOARD = Path(__file__).resolve().parent
_KPIHUB = _DASHBOARD.parent
_PYTHON = _KPIHUB / "Python"


def activate() -> None:
    for path in (_DASHBOARD, _PYTHON):
        s = str(path)
        if path.is_dir() and s not in sys.path:
            sys.path.insert(0, s)

    # KPIHub_PostgreSQL_Conn reads KPIHUB_*; Docker Compose often sets PG* only.
    for src, dst in (
        ("PGHOST", "KPIHUB_HOST"),
        ("PGPORT", "KPIHUB_PORT"),
        ("PGDATABASE", "KPIHUB_DATABASE"),
        ("PGUSER", "KPIHUB_USER"),
        ("PGPASSWORD", "KPIHUB_PASSWORD"),
    ):
        if os.environ.get(src):
            os.environ[dst] = os.environ[src]
    os.environ.setdefault("KPIHUB_HOST", os.environ.get("PGHOST", "localhost"))
    os.environ.setdefault("KPIHUB_DATABASE", os.environ.get("PGDATABASE", "KPIHub_EU"))
    os.environ.setdefault("KPIHUB_USER", os.environ.get("PGUSER", "dash_readonly"))
    os.environ.setdefault("KPIHUB_PASSWORD", os.environ.get("PGPASSWORD", ""))