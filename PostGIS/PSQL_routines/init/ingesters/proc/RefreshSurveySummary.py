#!/usr/bin/env python3
"""Refresh kpihub MV_SurveySummary_* using SurveySummaryIngester logic."""
from __future__ import annotations

import argparse
import os
import sys

_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_packages = os.path.abspath(os.path.join(_root, "..", "packages"))
for path in (_root, os.path.join(_root, "lib"), _packages):
  if path not in sys.path:
    sys.path.insert(0, path)

from locallib.picarrodb import Query
from lib.PostGISConnection import get_postgis_conn
from lib.SurveySummaryPostGISIngester import SurveySummaryPostGISIngester


def get_postgis_customers(conn, customer_name: str | None = None, customer_id: str | None = None):
  filters = ["active IS TRUE", "dblocation IN ('EU1', 'EU2')"]
  if customer_id:
    filters.append(f"customerid = '{customer_id}'")
  if customer_name:
    filters.append(f"lower(\"Name\") = lower('{customer_name.replace(chr(39), chr(39)*2)}')")

  query = f"""
    SELECT
      customerid AS "CustomerId",
      "Name",
      shortname AS "ShortName",
      active AS "Active",
      dblocation AS "DBLocation"
    FROM kpihub."KPI_Customer"
    WHERE {' AND '.join(filters)}
    ORDER BY "Name"
  """
  return Query(query=query).execute(conn)


def refresh_customer(customer_row, postgis_conn) -> int:
  arguments = {"conn": postgis_conn, "postgis_conn": postgis_conn}
  ingester = SurveySummaryPostGISIngester(arguments)
  ingester.set_customer_info(customer_row.to_dict())
  ingester.update_check()
  ingester.query_data()
  ingester.push_data()
  ingester.sanity_check()
  if ingester.check_flag and "output" in ingester.data:
    return len(ingester.data["output"])
  return 0


def main() -> int:
  parser = argparse.ArgumentParser(
    description="Populate kpihub MV_SurveySummary tables from LSDB using Python ingester logic."
  )
  parser.add_argument("--customer-name", help="Process one customer by name")
  parser.add_argument("--customer-id", help="Process one customer by UUID")
  parser.add_argument(
    "--all",
    action="store_true",
    help="Process all active EU1/EU2 customers",
  )
  args = parser.parse_args()

  if not args.all and not args.customer_name and not args.customer_id:
    parser.error("Provide --customer-name, --customer-id, or --all")

  postgis_conn = get_postgis_conn()
  customers = get_postgis_customers(
    postgis_conn,
    customer_name=args.customer_name,
    customer_id=args.customer_id,
  )

  if customers.empty:
    raise SystemExit("No matching active customers found in kpihub.KPI_Customer")

  total_rows = 0
  for _, customer in customers.iterrows():
    print(f"Processing {customer['Name']} ({customer['DBLocation']})...")
    total_rows += refresh_customer(customer, postgis_conn)

  print(f"Done. Inserted/updated {total_rows} survey summary rows.")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
