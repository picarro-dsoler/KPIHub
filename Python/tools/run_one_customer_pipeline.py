#!/usr/bin/env python3
"""Run IngestionProcess, KPIProcessing, ExcelOutput for one customer."""

from __future__ import annotations

import os
import runpy
import sys

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, _ROOT)

from bootstrap_paths import activate  # noqa: E402

activate()

ONLY = os.environ.get("KPIHUB_CUSTOMER_ONLY", "").strip()
if not ONLY:
    raise SystemExit("Set KPIHUB_CUSTOMER_ONLY to the customer Name (e.g. 'Wales and West Utilities').")

import lib.config as config  # noqa: E402

# Legacy code paths expect KPIHub_Conn; Postgres uses KPIHUB_CONNECTION.
config.KPIHub_Conn = config.KPIHUB_CONNECTION

import lib.handlers.CustomerHandler as customer_handler  # noqa: E402

_orig_get_customer_list = customer_handler.get_customer_list


def _filtered_customer_list(*args, **kwargs):
    # ExcelOutput passes KPIHub_Conn; the handler ignores it.
    df = _orig_get_customer_list()
    return df[df["Name"] == ONLY].reset_index(drop=True)


customer_handler.get_customer_list = _filtered_customer_list

_DEFAULT_SCRIPTS = ("IngestionProcess", "KPIProcessing", "ExcelOutput")

if __name__ == "__main__":
    script_env = os.environ.get("KPIHUB_RUN_SCRIPTS", "").strip()
    scripts = tuple(s.strip() for s in script_env.split(",") if s.strip()) or _DEFAULT_SCRIPTS
    for name in scripts:
        path = os.path.join(_ROOT, "processes", "global", f"{name}.py")
        print(f"\n{'=' * 60}\n{name}\n{'=' * 60}\n")
        runpy.run_path(path, run_name="__main__")