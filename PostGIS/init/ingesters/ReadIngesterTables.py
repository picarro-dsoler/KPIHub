"""Generate PostgreSQL CREATE TABLE DDL from IngesterTables via KPITable.create_table."""
import os
import sys

directory = os.path.abspath(os.path.dirname(__file__))
_root = os.path.abspath(os.path.join(directory, "..", ".."))
sys.path.insert(0, _root)

from lib.tables.IngesterTables import *

# Tables and optional composite primary keys (same as init/Setup.py)
TABLES = [
    (KPI_Customer, None),
    (KPI_POR, ["CustomerId", "Year"]),
    (KPI_OutputExcelLocation, None),
    (KPI_ReportDrivingSurvey, None),
    (KPI_Utilization, None),
    (KPI_ReportSummary, None),
    (KPI_PeakSATLocation, None),
    (KPI_PeakAboveSAT, None),
    (KPI_EmissionSourceSummary, None),
    (KPI_SurveySummary, ["SurveyId", "ReportId"]),
    (KPI_Definition, None),
    (KPI_Data, None),
]

PG_TYPE_MAP = {
    "uniqueidentifier": "UUID",
    "nvarchar": "TEXT",
    "varchar": "TEXT",
    "bit": "BOOLEAN",
    "datetime": "TIMESTAMP",
    "float": "DOUBLE PRECISION",
    "bigint": "BIGINT",
    "int": "INTEGER",
    "date": "date",
    "geometry": "geometry",
}

# PostgreSQL reserved / problematic identifiers (checked case-insensitively)
RESERVED_WORDS = {
    "all", "analyse", "analyze", "and", "any", "array", "as", "asc", "authorization",
    "binary", "both", "case", "cast", "check", "collate", "column", "constraint",
    "create", "cross", "current_catalog", "current_date", "current_role",
    "current_schema", "current_time", "current_timestamp", "current_user", "date",
    "default", "desc", "distinct", "end", "false", "foreign", "from", "grant",
    "group", "having", "in", "initially", "inner", "intersect", "into", "is", "join",
    "leading", "left", "like", "limit", "localtime", "localtimestamp", "name", "not",
    "null", "offset", "on", "or", "order", "outer", "overlaps", "placing", "primary",
    "references", "right", "select", "session_user", "some", "table", "then", "time",
    "timestamp", "to", "trailing", "true", "union", "unique", "user", "using", "value",
    "when", "where", "window", "with", "year",
}

SCHEMA = "kpihub"
OUTPUT_SQL = os.path.join(directory, "IngesterTables.sql")


def pg_ident(name):
    """Quote identifiers that collide with PostgreSQL reserved words or types."""
    if name.lower() in RESERVED_WORDS:
        return f'"{name}"'
    return name


def pg_column_type(datatype):
    if datatype is None:
        return "TEXT"
    return PG_TYPE_MAP.get(datatype, datatype)


def build_create_table(table, schema=SCHEMA, pair_key=None):
    col_defs = []
    for column in table.columns:
        col_defs.append(f"{pg_ident(column.name)} {pg_column_type(column.datatype)}")

    if pair_key is not None:
        pk_cols = pair_key
    else:
        pk_cols = [column.name for column in table.columns if getattr(column, "key", None) == "primary"]

    if pk_cols:
        pk = ", ".join(pg_ident(column) for column in pk_cols)
        col_defs.append(f"PRIMARY KEY ({pk})")

    body = ", ".join(col_defs)
    return f'CREATE TABLE IF NOT EXISTS "{schema}"."{table.name}" ({body})'


def main():
    statements = [
        "-- Auto-generated from lib/tables/IngesterTables.py",
        "-- Idempotent KPIHub table DDL for PostgreSQL/PostGIS",
        "-- Usage: psql -U dsoler -d Datanalytics -v ON_ERROR_STOP=1 -f IngesterTables.sql",
        "",
        f'CREATE SCHEMA IF NOT EXISTS "{SCHEMA}";',
        "",
    ]

    for table, pair_key in TABLES:
        statements.append(f"-- {table.name}")
        statements.append(build_create_table(table, pair_key=pair_key) + ";")
        statements.append("")

    statements.extend(
        [
            "-- Show kpihub tables with plain \\dt after reconnecting",
            "DO $$",
            "BEGIN",
            "  EXECUTE format(",
            "    'ALTER DATABASE %I SET search_path TO kpihub, public',",
            "    current_database()",
            "  );",
            "END $$;",
        ]
    )

    with open(OUTPUT_SQL, "w", encoding="utf-8") as f:
        f.write("\n".join(statements) + "\n")

    print(f"Wrote {OUTPUT_SQL}")


if __name__ == "__main__":
    main()
