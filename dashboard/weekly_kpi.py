"""Weekly_KPI via KPIHub Query / unified_query (same SQL as ExcelOutput.py)."""
from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from kpihub_query import unified_query

META_COLS = {"Year", "PeriodValue", "CustomerName", "BoundaryRegion", "WeekDates"}
# Shown in the excel-type grid (CustomerName omitted — already chosen in the filter).
DISPLAY_META_COLS = ("WeekDates", "Year", "PeriodValue", "BoundaryRegion")
# No separate tab for these KPI_Definition.Type values.
EXCLUDED_KPI_TYPES = frozenset({"Period"})


def week_dates(year: int, week: int) -> tuple[date, date]:
    year = int(year)
    week = int(week)
    week_start = date.fromisocalendar(year, week, 1)
    week_end = week_start + timedelta(days=6)
    min_start = date(year, 1, 1)
    if week_start < min_start:
        week_start = min_start
        week_end = week_start + timedelta(days=6)
    return week_start, week_end


def max_iso_week(year: int) -> int:
    return date(year, 12, 28).isocalendar()[1]


def expected_weeks(year: int, as_of: date | None = None) -> list[int]:
    as_of = as_of or date.today()
    last_week = max_iso_week(year)
    if as_of.year < year:
        return []
    if as_of.year > year:
        return list(range(1, last_week + 1))
    return list(range(1, min(as_of.isocalendar()[1], last_week) + 1))


def ensure_all_weeks(
    export_df: pd.DataFrame | None,
    year: int,
    customer_name: str,
    region,
    weeks: list[int] | None = None,
    value_columns: list[str] | None = None,
) -> pd.DataFrame:
    weeks = weeks if weeks is not None else expected_weeks(year)
    template = pd.DataFrame({"PeriodValue": weeks})

    if export_df is None or export_df.empty:
        filled = template.copy()
    else:
        export_df = export_df.copy()
        export_df["PeriodValue"] = export_df["PeriodValue"].astype(int)
        filled = template.merge(export_df, on="PeriodValue", how="left")

    filled["Year"] = year
    filled["CustomerName"] = customer_name
    filled["BoundaryRegion"] = region

    if value_columns:
        for col in value_columns:
            if col not in META_COLS and col not in filled.columns:
                filled[col] = 0

    value_cols = [c for c in filled.columns if c not in META_COLS]
    for col in value_cols:
        filled[col] = pd.to_numeric(filled[col], errors="coerce").fillna(0)

    meta_order = [c for c in ["Year", "PeriodValue", "CustomerName", "BoundaryRegion"] if c in filled.columns]
    other = [c for c in filled.columns if c not in meta_order]
    filled = filled[meta_order + other].sort_values("PeriodValue").reset_index(drop=True)
    return filled


def _sql_literal(value: str) -> str:
    return str(value).replace("'", "''")


def list_customers() -> pd.DataFrame:
    df = unified_query("SELECT * FROM KPI_Customer WHERE DBLocation <> 'Unknown'")
    if "Active" not in df.columns:
        return df
    active = df["Active"]
    if active.dtype == bool:
        return df[active].copy()
    return df[active.astype(int) == 1].copy()


def weekly_kpi_column_names() -> list[str]:
    """Column list from Weekly_KPI (Postgres search_path / SQLite view)."""
    probe = unified_query("SELECT * FROM Weekly_KPI LIMIT 1")
    if not probe.empty:
        return probe.columns.tolist()
    cols = unified_query(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name ILIKE 'weekly_kpi' "
        "ORDER BY ordinal_position"
    )
    if cols.empty:
        raise RuntimeError("Weekly_KPI has no columns (view missing or empty).")
    name_col = "column_name" if "column_name" in cols.columns else cols.columns[0]
    return cols[name_col].astype(str).tolist()


def load_kpi_definitions() -> pd.DataFrame:
    return unified_query("SELECT Name, Unit, Description, Formula, Type FROM KPI_Definition")


def distinct_regions(customer_name: str) -> list:
    name = _sql_literal(customer_name)
    df = unified_query(f"SELECT DISTINCT BoundaryRegion FROM Weekly_KPI WHERE CustomerName = '{name}'")
    if df.empty or "BoundaryRegion" not in df.columns:
        return [None]
    regions = df["BoundaryRegion"].tolist()
    return regions if regions else [None]


def load_weekly_kpi(customer_name: str, year: int) -> pd.DataFrame:
    name = _sql_literal(customer_name)
    return unified_query(
        f"SELECT * FROM Weekly_KPI WHERE CustomerName = '{name}' AND Year = {int(year)}"
    )


def region_label(region) -> str:
    if region is None or (isinstance(region, float) and pd.isna(region)):
        return "Global"
    return str(region)


def _kpi_columns_by_type(kpi_defs: pd.DataFrame) -> dict[str, list[str]]:
    """Map KPI_Definition.Type -> KPI column names (Weekly_KPI value columns)."""
    by_type: dict[str, list[str]] = {}
    has_type = "Type" in kpi_defs.columns
    for _, row in kpi_defs.iterrows():
        name = row.get("Name")
        if name is None or (isinstance(name, float) and pd.isna(name)):
            continue
        name = str(name)
        if has_type and pd.notna(row.get("Type")) and str(row.get("Type")).strip():
            kpi_type = str(row["Type"]).strip()
        else:
            kpi_type = "Other"
        by_type.setdefault(kpi_type, []).append(name)
    return by_type


def _format_display(export_df: pd.DataFrame, unit_by_name: dict[str, str]) -> tuple[pd.DataFrame, dict[str, str]]:
    units = {col: unit_by_name.get(col, "") for col in export_df.columns}
    display = export_df.copy()
    for col in display.columns:
        if col not in META_COLS and col != "WeekDates":
            display[col] = display[col].map(lambda v: f"{float(v):g}" if pd.notna(v) else "0")
    return display, units


def _prepare_export_df(
    customer_name: str,
    year: int,
    region,
) -> tuple[pd.DataFrame, dict[str, str]]:
    weeks = expected_weeks(year)
    view_cols = weekly_kpi_column_names()
    value_columns = [c for c in view_cols if c not in META_COLS]

    kpi_defs = load_kpi_definitions()
    unit_by_name = {
        str(row["Name"]): row["Unit"]
        for _, row in kpi_defs.iterrows()
        if pd.notna(row.get("Name"))
    }

    kpi_data = load_weekly_kpi(customer_name, year)
    if pd.isnull(region):
        export_df = kpi_data[kpi_data["BoundaryRegion"].isnull()].copy() if not kpi_data.empty else pd.DataFrame()
    else:
        export_df = kpi_data[kpi_data["BoundaryRegion"] == region].copy() if not kpi_data.empty else pd.DataFrame()

    export_df = ensure_all_weeks(
        export_df,
        year=year,
        customer_name=customer_name,
        region=region,
        weeks=weeks,
        value_columns=value_columns,
    )

    if "PeakAboveSATCount" in export_df.columns:
        export_df["PeakAboveSATCount"] = export_df["PeakAboveSATCount"].fillna(0)

    export_df["WeekDates"] = export_df["PeriodValue"].apply(
        lambda w: f"{week_dates(year, int(w))[0]} to {week_dates(year, int(w))[1]}"
    )
    col_order = list(export_df.columns)
    if "WeekDates" in col_order:
        col_order.insert(0, col_order.pop(col_order.index("WeekDates")))
        export_df = export_df[col_order]

    return export_df, unit_by_name


def build_excel_sheets_by_type(
    customer_name: str,
    year: int,
    region,
) -> dict[str, tuple[pd.DataFrame, dict[str, str]]]:
    """One excel-type table per KPI_Definition.Type (meta columns + KPIs of that type)."""
    export_df, unit_by_name = _prepare_export_df(customer_name, year, region)
    kpi_defs = load_kpi_definitions()
    by_type = _kpi_columns_by_type(kpi_defs)

    meta_leading = [c for c in DISPLAY_META_COLS if c in export_df.columns]

    assigned: set[str] = set()
    sheets: dict[str, tuple[pd.DataFrame, dict[str, str]]] = {}

    type_order = sorted(by_type.keys(), key=lambda t: (t == "Other", t.lower()))
    for kpi_type in type_order:
        if kpi_type in EXCLUDED_KPI_TYPES:
            assigned.update(c for c in by_type[kpi_type] if c in export_df.columns)
            continue
        wanted = [c for c in by_type[kpi_type] if c in export_df.columns]
        assigned.update(wanted)
        if not wanted and kpi_type != "Other":
            continue
        cols = meta_leading + wanted
        slice_df = export_df[cols].copy()
        display, units = _format_display(slice_df, unit_by_name)
        sheets[kpi_type] = (display, units, slice_df.copy())

    if not sheets:
        disp, u = _format_display(export_df.copy(), unit_by_name)
        sheets["All KPIs"] = (disp, u, export_df.copy())

    return sheets


def build_excel_sheet(
    customer_name: str,
    year: int,
    region,
) -> tuple[pd.DataFrame, dict[str, str]]:
    """Full wide sheet (all KPI columns) — used when Type grouping is not needed."""
    export_df, unit_by_name = _prepare_export_df(customer_name, year, region)
    return _format_display(export_df, unit_by_name)