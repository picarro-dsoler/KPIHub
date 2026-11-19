#!/usr/bin/env python3
"""KPIHub command-line entrypoint (schema maintenance, init helpers)."""

from __future__ import annotations

import argparse
import os
import sys

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, _ROOT)

from bootstrap_paths import activate  # noqa: E402

activate()

from lib.tables.IngesterTables import dbo  # noqa: E402
from lib.tables.TableConfig import TABLE_CONFIG_LIST  # noqa: E402


def _primary_key_by_table():
    return {cfg["Name"]: cfg["PrimaryKey"] for cfg in TABLE_CONFIG_LIST}


def restart_tables(table_names: list[str] | None = None, *, confirmed: bool) -> None:
    """Drop and recreate KPI Hub tables (same logic as init/Setup.py)."""
    pk_by_table = _primary_key_by_table()
    names = sorted(table_names or dbo.keys())
    unknown = [n for n in names if n not in dbo]
    if unknown:
        raise SystemExit(f"Unknown table(s): {', '.join(unknown)}")

    if not confirmed:
        print("This will DROP and recreate the following table(s) on KPIHUB_CONNECTION:")
        for name in names:
            print(f"  - {name}")
        reply = input("Type 'yes' to continue: ").strip().lower()
        if reply != "yes":
            raise SystemExit("Aborted.")

    for table_name in names:
        pk = pk_by_table.get(table_name)
        table = dbo[table_name]
        if isinstance(pk, list):
            table.reinit_table(arguments={"pair_key": pk})
        else:
            table.reinit_table()
        print(f"Reinitialized {table_name}")

    print(f"Done. {len(names)} table(s) restarted.")


def cmd_restart_tables(args: argparse.Namespace) -> None:
    names = args.table if args.table else None
    restart_tables(names, confirmed=args.yes)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="KPIHubCLI",
        description="KPIHub maintenance utilities.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    restart = sub.add_parser(
        "restart-tables",
        help="Drop and recreate KPI Hub tables (destructive).",
    )
    restart.add_argument(
        "--table",
        "-t",
        action="append",
        metavar="NAME",
        help="Only restart this table (repeat for multiple). Default: all dbo tables.",
    )
    restart.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Skip confirmation prompt.",
    )
    restart.set_defaults(func=cmd_restart_tables)

    list_tables = sub.add_parser("list-tables", help="List tables known to dbo.")
    list_tables.set_defaults(func=lambda _a: print("\n".join(sorted(dbo.keys()))))

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()