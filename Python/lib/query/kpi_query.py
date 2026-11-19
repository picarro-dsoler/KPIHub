from locallib.query import Query

from lib.config import KPIHUB_CONNECTION
from lib.KPIHubConnection import PostgreSQLConnection


def unified_query(sql, connection=KPIHUB_CONNECTION):
    df = Query(query=sql).execute(connection)
    if isinstance(connection, PostgreSQLConnection):
        from lib.tables.IngesterTables import column_name_map
        df.columns = [column_name_map[str(col).lower()] for col in df.columns]
        # Uppercase UUID-style identifier columns only (not e.g. IdleTimeMinutes).
        for col in df.columns:
            if col == "Id" or col.endswith("Id"):
                df[col] = df[col].astype(str).str.upper()
    return df