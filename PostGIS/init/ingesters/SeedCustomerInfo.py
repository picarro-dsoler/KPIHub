"""Seed kpihub tables from CustomerInfo.csv using eu1/eu2 foreign tables for CustomerId."""
from __future__ import annotations

import csv
import os
import subprocess
import sys
from datetime import datetime

directory = os.path.abspath(os.path.dirname(__file__))
_root = os.path.abspath(os.path.join(directory, "..", ".."))
CSV_PATH = os.path.join(_root, "CustomerInfo.csv")
OUTPUT_SQL = os.path.join(directory, "SeedCustomerInfo.sql")

PG_HOST = os.environ.get("PGHOST", "localhost")
PG_PORT = os.environ.get("PGPORT", "5432")
PG_USER = os.environ.get("PGUSER", "dsoler")
PG_PASSWORD = os.environ.get("PGPASSWORD", "dsoler")
PG_DATABASE = os.environ.get("PGDATABASE", "Datanalytics")


def sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def run_psql(sql: str, capture: bool = True) -> str:
    env = os.environ.copy()
    env["PGPASSWORD"] = PG_PASSWORD
    result = subprocess.run(
        [
            "psql",
            "-h",
            PG_HOST,
            "-p",
            PG_PORT,
            "-U",
            PG_USER,
            "-d",
            PG_DATABASE,
            "-v",
            "ON_ERROR_STOP=1",
            "-t",
            "-A",
            "-c",
            sql,
        ],
        env=env,
        capture_output=capture,
        text=True,
        check=True,
    )
    return result.stdout.strip() if capture else ""


def lookup_customer_id(customer_name: str, db_location: str) -> tuple[str, str]:
    schema = "eu2" if db_location.upper() == "EU2" else "eu1"
    sql = f"""
    SELECT "Id"::text || '|' || "Name"
    FROM {schema}."Customer"
    WHERE lower("Name") = lower({sql_literal(customer_name)})
    LIMIT 1;
    """
    row = run_psql(sql)
    if not row:
        raise ValueError(
            f"Customer '{customer_name}' not found in {schema}.\"Customer\""
        )
    customer_id, lsdb_name = row.split("|", 1)
    return customer_id, lsdb_name


def parse_bool(value: str) -> bool:
    return str(value).strip() in {"1", "true", "True", "TRUE", "yes", "Yes"}


def parse_optional_int(value: str) -> int | None:
    value = (value or "").strip()
    if not value:
        return None
    return int(value)


def parse_optional_float(value: str) -> float | None:
    value = (value or "").strip()
    if not value:
        return None
    return float(value)


def parse_optional_date(value: str) -> str | None:
    value = (value or "").strip()
    if not value:
        return None
    return datetime.strptime(value, "%d-%m-%Y").strftime("%Y-%m-%d")


def short_name(name: str) -> str:
    return "".join(name.split())


def load_rows() -> list[dict[str, str]]:
    with open(CSV_PATH, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def build_seed_sql(rows: list[dict[str, str]]) -> str:
    statements = [
        "-- Auto-generated from CustomerInfo.csv",
        "-- Usage: psql -U dsoler -d Datanalytics -v ON_ERROR_STOP=1 -f SeedCustomerInfo.sql",
        "",
        "SET enable_mergejoin = off;",
        "",
    ]

    for row in rows:
        customer_name = row["CustomerName"].strip()
        db_location = row["DBLocation"].strip().upper()
        schema = "eu2" if db_location == "EU2" else "eu1"
        is_active = parse_bool(row.get("IsActive", "0"))
        box_folder = (row.get("OutputExcelFolder") or "").strip()
        working_hours = parse_optional_int(row.get("WorkingHours"))
        working_days = parse_optional_int(row.get("WorkingDays"))
        base_surveyors = parse_optional_int(row.get("BaseSurveyors"))
        por_value = parse_optional_float(row.get("POR"))
        por_year = parse_optional_int(row.get("PORYear"))
        por_start = parse_optional_date(row.get("PORStartingDate"))
        por_end = parse_optional_date(row.get("POREndingDate"))

        statements.append(f"-- {customer_name} ({db_location})")
        statements.append(
            f"""
WITH src AS (
  SELECT
    C."Id" AS customerid,
    C."Name" AS customer_name,
    {sql_literal(db_location)}::text AS dblocation,
    {str(is_active).lower()}::boolean AS active
  FROM {schema}."Customer" C
  WHERE lower(C."Name") = lower({sql_literal(customer_name)})
)
INSERT INTO kpihub."KPI_Customer" (
  customerid, "Name", shortname, active, dblocation, lastupdated
)
SELECT
  customerid,
  customer_name,
  regexp_replace(customer_name, '\\s+', '', 'g'),
  active,
  dblocation,
  NOW()
FROM src
ON CONFLICT (customerid) DO UPDATE SET
  "Name" = EXCLUDED."Name",
  shortname = EXCLUDED.shortname,
  active = EXCLUDED.active,
  dblocation = EXCLUDED.dblocation,
  lastupdated = EXCLUDED.lastupdated;
""".strip()
        )

        if box_folder:
            statements.append(
                f"""
INSERT INTO kpihub."KPI_OutputExcelLocation" (customerid, boxfolderid, lastupdated)
SELECT C."Id", {sql_literal(box_folder)}, NOW()
FROM {schema}."Customer" C
WHERE lower(C."Name") = lower({sql_literal(customer_name)})
ON CONFLICT (customerid) DO UPDATE SET
  boxfolderid = EXCLUDED.boxfolderid,
  lastupdated = EXCLUDED.lastupdated;
""".strip()
            )

        if working_hours is not None and working_days is not None:
            base_surveyor_sql = (
                str(base_surveyors) if base_surveyors is not None else "NULL"
            )
            statements.append(
                f"""
INSERT INTO kpihub."KPI_Utilization" (
  customerid, workingdays, workinghours, sunrisehour, sunsethour,
  basesurveyorcount, description, lastupdated
)
SELECT
  C."Id",
  {working_days},
  {working_hours},
  6,
  20,
  {base_surveyor_sql},
  {sql_literal(customer_name)},
  NOW()
FROM {schema}."Customer" C
WHERE lower(C."Name") = lower({sql_literal(customer_name)})
ON CONFLICT (customerid) DO UPDATE SET
  workingdays = EXCLUDED.workingdays,
  workinghours = EXCLUDED.workinghours,
  basesurveyorcount = EXCLUDED.basesurveyorcount,
  description = EXCLUDED.description,
  lastupdated = EXCLUDED.lastupdated;
""".strip()
            )

        if por_value is not None and por_year is not None and por_start and por_end:
            statements.append(
                f"""
INSERT INTO kpihub."KPI_POR" (
  customerid, "Year", startingdate, endingdate, description, "Value", unit, lastupdated
)
SELECT
  C."Id"::text,
  {por_year},
  {sql_literal(por_start)}::timestamp,
  {sql_literal(por_end)}::timestamp,
  {sql_literal(f'{customer_name} POR {por_year}')},
  {por_value},
  'Km',
  NOW()
FROM {schema}."Customer" C
WHERE lower(C."Name") = lower({sql_literal(customer_name)})
ON CONFLICT (customerid, "Year") DO UPDATE SET
  startingdate = EXCLUDED.startingdate,
  endingdate = EXCLUDED.endingdate,
  description = EXCLUDED.description,
  "Value" = EXCLUDED."Value",
  unit = EXCLUDED.unit,
  lastupdated = EXCLUDED.lastupdated;
""".strip()
            )

        statements.append("")

    return "\n\n".join(statements) + "\n"


def seed(execute: bool = True) -> None:
    rows = load_rows()
    sql = build_seed_sql(rows)

    with open(OUTPUT_SQL, "w", encoding="utf-8") as handle:
        handle.write(sql)
    print(f"Wrote {OUTPUT_SQL}")

    if not execute:
        return

    env = os.environ.copy()
    env["PGPASSWORD"] = PG_PASSWORD
    subprocess.run(
        [
            "psql",
            "-h",
            PG_HOST,
            "-p",
            PG_PORT,
            "-U",
            PG_USER,
            "-d",
            PG_DATABASE,
            "-v",
            "ON_ERROR_STOP=1",
            "-f",
            OUTPUT_SQL,
        ],
        env=env,
        check=True,
    )

    count = run_psql('SELECT COUNT(*) FROM kpihub."KPI_Customer";')
    active_count = run_psql(
        'SELECT COUNT(*) FROM kpihub."KPI_Customer" WHERE active IS TRUE;'
    )
    print(f"KPI_Customer rows: {count} (active: {active_count})")


if __name__ == "__main__":
    write_only = "--sql-only" in sys.argv
    seed(execute=not write_only)
