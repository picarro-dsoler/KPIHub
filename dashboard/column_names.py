"""Map Postgres lowercase columns to KPIHub names via KPI_Definition (+ table DDL)."""
from __future__ import annotations

from functools import lru_cache

import pandas as pd

from db_conn import KPIHUB_CONNECTION


@lru_cache(maxsize=1)
def column_name_map() -> dict[str, str]:
    mapping: dict[str, str] = {}
    try:
        from lib.tables.TableConfig import TABLE_CONFIG_LIST  # noqa: E402

        for cfg in TABLE_CONFIG_LIST:
            for col in cfg["Columns"]:
                mapping[str(col).lower()] = col
    except Exception:
        pass

    with KPIHUB_CONNECTION.engine.connect() as conn:
        defs = pd.read_sql("SELECT Name FROM KPI_Definition", conn)
    name_col = next((c for c in defs.columns if str(c).lower() == "name"), None)
    if name_col is not None:
        for name in defs[name_col].dropna().astype(str):
            mapping[str(name).lower()] = str(name)

    return mapping


def normalize_dataframe(df):
    cmap = column_name_map()
    df = df.copy()
    df.columns = [cmap.get(str(c).lower(), str(c)) for c in df.columns]
    for col in df.columns:
        if col == "Id" or col.endswith("Id"):
            df[col] = df[col].astype(str).str.upper()
    return df


def refresh_column_name_cache() -> None:
    column_name_map.cache_clear()