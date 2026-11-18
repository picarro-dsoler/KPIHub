"""
PostgreSQL KPITable: same method names as lib/tables/KPITable.py (SQLite) but targets Postgres.

arguments use:
  - 'conn' or 'dsn' or env-based connect (see connection.get_conn_from_arguments)
  - 'schema' (optional, default 'public') for CREATE/DROP/INSERT
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, time

import pandas as pd

from .db_table import DBTable
from .connection import get_conn_from_arguments

# SQL Server-style datatypes (as in IngesterTables) -> PostgreSQL
PG_TYPE_MAP = {
    "uniqueidentifier": "UUID",
    "nvarchar": "TEXT",
    "varchar": "TEXT",
    "int": "INTEGER",
    "bigint": "BIGINT",
    "float": "DOUBLE PRECISION",
    "real": "REAL",
    "bit": "BOOLEAN",
    "datetime": "TIMESTAMPTZ",
    "date": "DATE",
    "time": "TIME",
    "geometry": "TEXT",  # WKT; use PostGIS geometry if you migrate column types
}


def _quote_ident(name: str) -> str:
    if not name.replace("_", "").isalnum():
        raise ValueError(f"Invalid SQL identifier: {name!r}")
    return '"' + name.replace('"', '""') + '"'


def _qualified_name(schema: str, table: str) -> str:
    return f"{_quote_ident(schema)}.{_quote_ident(table)}"


class KPITable(DBTable):
    def __init__(self, name, columns=None):
        super().__init__(name, columns)
        self.sql_list = {}

    @staticmethod
    def pg_column_type(datatype):
        if datatype is None:
            return "TEXT"
        return PG_TYPE_MAP.get(datatype, datatype)

    def _schema(self, arguments):
        return arguments.get("schema", "public") if arguments else "public"

    def delete_table(self, arguments=None):
        if arguments is None:
            raise ValueError("Arguments are required")
        schema = self._schema(arguments)
        conn = get_conn_from_arguments(arguments)
        own_conn = arguments.get("conn") is None
        try:
            with conn.cursor() as cur:
                qn = _qualified_name(schema, self.name)
                cur.execute(f"DROP TABLE IF EXISTS {qn} CASCADE")
            conn.commit()
        finally:
            if own_conn:
                conn.close()

    def create_table(self, arguments=None, commit=True):
        if arguments is None:
            raise ValueError("Arguments are required")
        schema = self._schema(arguments)
        conn = get_conn_from_arguments(arguments)
        own_conn = arguments.get("conn") is None

        col_defs_list = []
        primary_keys = []
        for column in self.columns:
            pg_type = self.pg_column_type(column.datatype)
            col_def = f'"{column.name}" {pg_type}'
            if getattr(column, "key", None) == "primary":
                primary_keys.append(column.name)
            col_defs_list.append(col_def)
        col_defs = ", ".join(col_defs_list)
        if primary_keys:
            pk_quoted = ", ".join(f'"{pk}"' for pk in primary_keys)
            col_defs += f", PRIMARY KEY ({pk_quoted})"
        if arguments.get("pair_key") is not None:
            pk_quoted = ", ".join(f'"{c}"' for c in arguments["pair_key"])
            col_defs += f", PRIMARY KEY ({pk_quoted})"

        qn = _qualified_name(schema, self.name)
        sql = f"CREATE TABLE IF NOT EXISTS {qn} ({col_defs})"

        if commit:
            try:
                with conn.cursor() as cur:
                    cur.execute(f"CREATE SCHEMA IF NOT EXISTS {_quote_ident(schema)}")
                    cur.execute(sql)
                    if arguments.get("extra_sql"):
                        cur.execute(arguments["extra_sql"])
                conn.commit()
            finally:
                if own_conn:
                    conn.close()
        return sql

    def reinit_table(self, arguments=None, extra_sql=None):
        if arguments is None:
            raise ValueError("Arguments are required")
        arguments = dict(arguments)
        if extra_sql is not None:
            arguments["extra_sql"] = extra_sql
        self.delete_table(arguments=arguments)
        self.create_table(arguments=arguments)

    def query_table(self, arguments=None):
        if arguments is None:
            raise ValueError("Arguments are required")
        schema = self._schema(arguments)
        conn = get_conn_from_arguments(arguments)
        own_conn = arguments.get("conn") is None
        try:
            qn = _qualified_name(schema, self.name)
            df = pd.read_sql_query(f"SELECT * FROM {qn}", conn)
            return df
        finally:
            if own_conn:
                conn.close()

    def sql(self, query="create", db_type="postgres"):
        return self.sql_list[query]

    def update_table(self, arguments=None):
        if arguments is None:
            raise ValueError("Arguments are required")
        df = arguments["DataFrame"]
        primary_key = arguments["PrimaryKey"]
        schema = self._schema(arguments)

        if isinstance(primary_key, list):
            pk_cols = set(primary_key)
            primary_key_str = ",".join(f'"{c}"' for c in primary_key)
        elif isinstance(primary_key, str):
            pk_cols = {primary_key}
            primary_key_str = f'"{primary_key}"'
        else:
            raise ValueError("PrimaryKey must be a list of strings or a single string")

        conn = get_conn_from_arguments(arguments)
        own_conn = arguments.get("conn") is None

        cols = df.columns.tolist()
        col_list_q = ", ".join(f'"{c}"' for c in cols)
        placeholders = ", ".join(["%s"] * len(cols))
        updates = ", ".join(
            [f'"{col}"=EXCLUDED."{col}"' for col in cols if col not in pk_cols]
        )

        qn = _qualified_name(schema, self.name)
        insert_sql = f"""
            INSERT INTO {qn} ({col_list_q})
            VALUES ({placeholders})
            ON CONFLICT({primary_key_str}) DO UPDATE SET
            {updates};
        """

        def clean_value(val):
            if pd.isna(val):
                return None
            if isinstance(val, pd.Timestamp):
                return val.to_pydatetime()
            if isinstance(val, datetime):
                return val
            if isinstance(val, time):
                return val
            if isinstance(val, date):
                return val
            if isinstance(val, uuid.UUID):
                return str(val)
            if hasattr(val, "wkt") and not isinstance(val, (str, bytes, bytearray)):
                return val.wkt
            if isinstance(val, (bytes, bytearray)):
                return bytes(val)
            if hasattr(val, "item"):
                return val.item()
            return val

        try:
            data = [tuple(clean_value(row[col]) for col in cols) for _, row in df.iterrows()]
            with conn.cursor() as cur:
                cur.executemany(insert_sql, data)
            conn.commit()
        finally:
            if own_conn:
                conn.close()

    def delete_data(self, arguments=None):
        if arguments is None:
            raise ValueError("Arguments are required")
        if "PrimaryKey" not in arguments:
            raise ValueError("PrimaryKey is required")
        if "KeyValues" not in arguments:
            raise ValueError("KeyValues is required (list of dicts or DataFrame)")

        schema = self._schema(arguments)
        primary_key = arguments["PrimaryKey"]
        key_values = arguments["KeyValues"]

        if isinstance(primary_key, list):
            pk_cols = primary_key
        elif isinstance(primary_key, str):
            pk_cols = [primary_key]
        else:
            raise ValueError("PrimaryKey must be a list of strings or a single string")

        if isinstance(key_values, pd.DataFrame):
            keys_list = key_values[pk_cols].to_dict(orient="records")
        elif isinstance(key_values, list):
            keys_list = key_values
        else:
            raise ValueError("KeyValues must be a DataFrame or list of dicts")

        conn = get_conn_from_arguments(arguments)
        own_conn = arguments.get("conn") is None

        where_clause = " AND ".join([f'"{col}" = %s' for col in pk_cols])
        qn = _qualified_name(schema, self.name)
        sql = f"DELETE FROM {qn} WHERE {where_clause}"

        try:
            values_list = []
            for key_dict in keys_list:
                values = tuple(key_dict.get(col) for col in pk_cols)
                values_list.append(values)
            with conn.cursor() as cur:
                cur.executemany(sql, values_list)
            conn.commit()
        finally:
            if own_conn:
                conn.close()
