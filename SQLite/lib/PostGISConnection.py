"""PostgreSQL / PostGIS connection for KPIHub snapshot tables."""
from __future__ import annotations

import os

from locallib.picarrodb import PConnection
from sqlalchemy import create_engine
from urllib.parse import quote_plus

PG_HOST = os.environ.get("PGHOST", "localhost")
PG_PORT = os.environ.get("PGPORT", "5432")
PG_USER = os.environ.get("PGUSER", "dsoler")
PG_PASSWORD = os.environ.get("PGPASSWORD", "dsoler")
PG_DATABASE = os.environ.get("PGDATABASE", "Datanalytics")


class PostGISConnection(PConnection):
    def __init__(
        self,
        host: str = PG_HOST,
        database: str = PG_DATABASE,
        user: str = PG_USER,
        password: str = PG_PASSWORD,
        port: str = PG_PORT,
    ):
        self.port = port
        super().__init__(host, database, user, password, dbtype="postgresql")

    def set_engine(self):
        user = quote_plus(self.user or "")
        password = quote_plus(self.password or "")
        database = quote_plus(self.database or "")
        return create_engine(
            f"postgresql+psycopg2://{user}:{password}@{self.host}:{self.port}/{database}"
        )


def get_postgis_conn() -> PostGISConnection:
    return PostGISConnection()
