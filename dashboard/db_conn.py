"""Postgres connection for dashboard (no locallib import — avoids gasanalytics)."""
from __future__ import annotations

import os
from urllib.parse import quote_plus

from sqlalchemy import create_engine

from kpihub_bootstrap import activate

activate()


class PostgresKPIHubConn:
    dbtype = "postgresql"

    def __init__(self) -> None:
        host = os.environ.get("KPIHUB_HOST", "localhost")
        database = os.environ.get("KPIHUB_DATABASE", "KPIHub_EU")
        user = os.environ.get("KPIHUB_USER", "dsoler")
        password = os.environ.get("KPIHUB_PASSWORD", "dsoler")
        port = os.environ.get("KPIHUB_PORT", os.environ.get("PGPORT", "5432"))
        user_q = quote_plus(user)
        password_q = quote_plus(password)
        db_q = quote_plus(database)
        self.engine = create_engine(
            f"postgresql+psycopg2://{user_q}:{password_q}@{host}:{port}/{db_q}"
        )


KPIHUB_CONNECTION = PostgresKPIHubConn()