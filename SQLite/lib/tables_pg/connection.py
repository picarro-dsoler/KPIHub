"""PostgreSQL connection using only env vars (no picarrodb / SQL Server)."""

from __future__ import annotations

import os
from typing import Any

try:
    import psycopg2
    import psycopg2.extensions
except ImportError as e:  # pragma: no cover
    psycopg2 = None  # type: ignore
    _psycopg_import_error = e
else:
    _psycopg_import_error = None


def connect_postgres(
    host: str | None = None,
    port: int | None = None,
    database: str | None = None,
    user: str | None = None,
    password: str | None = None,
) -> Any:
    """Open a psycopg2 connection. Credentials from args or PG* environment variables."""
    if psycopg2 is None:
        raise ImportError(
            "psycopg2 is required for KPIHub PostgreSQL tables. "
            "Install with: pip install psycopg2-binary"
        ) from _psycopg_import_error

    kwargs = {
        "host": host if host is not None else os.environ.get("PGHOST", "localhost"),
        "port": port if port is not None else int(os.environ.get("PGPORT", "5432")),
        "dbname": database if database is not None else os.environ.get("PGDATABASE", "postgres"),
        "user": user if user is not None else os.environ.get("PGUSER", "postgres"),
        "password": password if password is not None else os.environ.get("PGPASSWORD", ""),
    }
    conn = psycopg2.connect(**kwargs)
    conn.autocommit = False
    return conn


def get_conn_from_arguments(arguments: dict) -> Any:
    """
    Resolve a connection from KPITable-style arguments.

    Supported keys:
      - 'conn': existing psycopg2 connection (caller owns lifecycle)
      - 'dsn': PostgreSQL connection URI string
      - or omit and use connect_postgres() with env vars
    """
    if "conn" in arguments and arguments["conn"] is not None:
        return arguments["conn"]
    if "dsn" in arguments and arguments["dsn"]:
        if psycopg2 is None:
            raise ImportError(
                "psycopg2 is required. pip install psycopg2-binary"
            ) from _psycopg_import_error
        return psycopg2.connect(arguments["dsn"])
    return connect_postgres()
