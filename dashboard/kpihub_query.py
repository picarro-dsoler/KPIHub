"""unified_query for dashboard — pandas read_sql + KPIHub column normalization."""
from __future__ import annotations

import pandas as pd

from column_names import normalize_dataframe
from db_conn import KPIHUB_CONNECTION


def query(sql: str) -> pd.DataFrame:
    with KPIHUB_CONNECTION.engine.connect() as conn:
        return pd.read_sql(sql, conn)


def unified_query(sql: str, connection=KPIHUB_CONNECTION) -> pd.DataFrame:
    df = query(sql)
    return normalize_dataframe(df)