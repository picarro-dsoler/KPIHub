"""KPIHub Weekly_KPI dashboard — Excel-style weekly table (see processes/global/ExcelOutput.py)."""
from __future__ import annotations

import os
from datetime import date

import pandas as pd
import plotly.graph_objects as go
from dotenv import load_dotenv
import dash

load_dotenv()
from dash import Input, Output, State, dash_table, dcc, html

from theme import (
    CARD_STYLE,
    COLORS,
    DROPDOWN_STYLE,
    PAGE_STYLE,
    TABLE_STYLE_CELL,
    TABLE_STYLE_DATA,
    TABLE_STYLE_HEADER,
)
from weekly_kpi import (
    DISPLAY_META_COLS,
    META_COLS,
    build_excel_sheets_by_type,
    distinct_regions,
    list_customers,
    load_kpi_definitions,
    region_label,
)

PORT = int(os.environ.get("KPIHUB_DASH_PORT", "8052"))

dash_app = dash.Dash(__name__, suppress_callback_exceptions=True, title="KPIHub Weekly KPI")
server = dash_app.server

_default_year = int(os.environ.get("KPIHUB_DEFAULT_YEAR", str(date.today().year)))

try:
    _customers = list_customers()
    if _customers.empty:
        raise RuntimeError("No active customers in KPI_Customer (check DB / Active flag).")
    _customer_options = [
        {"label": str(r["Name"]), "value": str(r["Name"])} for _, r in _customers.iterrows()
    ]
    _default_customer = _customer_options[0]["value"] if _customer_options else None
    _db_ok = True
except Exception as exc:  # noqa: BLE001 — show wiring error in UI
    _db_ok = False
    _customer_options = []
    _default_customer = None
    _startup_error = str(exc)
else:
    _startup_error = None

_PLOT_PLACEHOLDER = {
    "layout": {
        "paper_bgcolor": COLORS["surface"],
        "plot_bgcolor": COLORS["surface_alt"],
        "font": {"color": COLORS["text"], "family": "Inter, Segoe UI, system-ui, sans-serif"},
        "margin": {"l": 48, "r": 24, "t": 40, "b": 48},
        "xaxis": {"title": "Week", "gridcolor": COLORS["border"], "linecolor": COLORS["border"]},
        "yaxis": {"title": "Value", "gridcolor": COLORS["border"], "linecolor": COLORS["border"]},
        "title": {"text": "Choose KPIs below to plot weekly values", "font": {"size": 14, "color": COLORS["muted"]}},
    }
}


def _header_label(col: str, units: dict[str, str]) -> str:
    unit = (units.get(col) or "").strip()
    if col in DISPLAY_META_COLS or not unit:
        return col
    return f"{col} ({unit})"


def _column_min_width_px(col: str, units: dict[str, str]) -> int:
    unit = ""
    if col not in DISPLAY_META_COLS:
        unit = (units.get(col) or "").strip() or "—"
    longest_line = max(len(col), len(unit), 6)
    if col == "WeekDates":
        return max(140, longest_line * 7 + 28)
    if col == "Year":
        return 72
    if col == "PeriodValue":
        return 88
    if col == "BoundaryRegion":
        return max(100, min(220, longest_line * 7 + 28))
    return min(380, max(100, longest_line * 7 + 32))


def _fixed_meta_count(df_columns: list[str]) -> int:
    n = 0
    for col in df_columns:
        if col in DISPLAY_META_COLS:
            n += 1
        else:
            break
    return n


def _multi_header_columns(df_columns: list[str], units: dict[str, str]) -> list[dict]:
    """Excel-style headers: row 1 = KPI / meta name, row 2 = unit (or blank for meta)."""
    out: list[dict] = []
    for col in df_columns:
        if col in DISPLAY_META_COLS:
            unit_row = ""
        else:
            unit_row = (units.get(col) or "").strip() or "—"
        out.append({"name": [col, unit_row], "id": col, "type": "text"})
    return out


def _excel_data_table(display, units, *, table_id: dict | str) -> dash_table.DataTable:
    df_columns = display.columns.tolist()
    columns = _multi_header_columns(df_columns, units)
    records = display.astype(str).to_dict("records")
    width_rules = [
        {
            "if": {"column_id": col},
            "minWidth": f"{_column_min_width_px(col, units)}px",
            "width": f"{_column_min_width_px(col, units)}px",
            "maxWidth": f"{_column_min_width_px(col, units)}px",
        }
        for col in df_columns
    ]
    fixed_n = _fixed_meta_count(df_columns)
    fixed_columns = {"headers": True, "data": fixed_n} if fixed_n > 0 else None
    header_styles = width_rules + [
        {
            "if": {"header_index": 1},
            "backgroundColor": COLORS["unit_row_bg"],
            "fontWeight": "600",
            "fontSize": "12px",
            "color": COLORS["muted"],
        },
    ]

    return dash_table.DataTable(
        id=table_id,
        columns=columns,
        data=records,
        merge_duplicate_headers=True,
        style_table={
            "overflowX": "auto",
            "width": "100%",
            "minWidth": "100%",
        },
        style_header=TABLE_STYLE_HEADER,
        style_cell={**TABLE_STYLE_CELL, "whiteSpace": "nowrap"},
        style_data=TABLE_STYLE_DATA,
        style_cell_conditional=width_rules,
        style_header_conditional=header_styles,
        fixed_rows={"headers": True},
        fixed_columns=fixed_columns,
        page_size=20,
        sort_action="native",
        filter_action="native",
        export_format="xlsx",
        tooltip_header={
            col: {
                "value": (
                    col
                    if col in DISPLAY_META_COLS
                    else f"{col}\n{(units.get(col) or '').strip() or '—'}"
                ),
                "type": "text",
            }
            for col in df_columns
        },
        tooltip_delay=0,
        tooltip_duration=None,
    )


def _plot_store_payload(
    sheets: dict[str, tuple[pd.DataFrame, dict[str, str], pd.DataFrame]],
) -> dict:
    out: dict = {}
    for kpi_type, (_, units, numeric) in sheets.items():
        records: list[dict] = []
        for _, row in numeric.iterrows():
            rec: dict = {}
            for c in numeric.columns:
                if c == "CustomerName":
                    continue
                v = row[c]
                if c == "PeriodValue":
                    rec[c] = int(v) if pd.notna(v) else None
                elif c in META_COLS:
                    rec[c] = "" if pd.isna(v) else str(v)
                else:
                    rec[c] = float(v) if pd.notna(v) else 0.0
            records.append(rec)
        out[kpi_type] = {"records": records, "units": units}
    return out


def _definitions_table() -> dash_table.DataTable:
    defs = load_kpi_definitions()
    if defs.empty:
        return dash_table.DataTable(data=[], columns=[])
    desc_cols = [
        {"name": "Key", "id": "Name"},
        {"name": "Type", "id": "Type"},
        {"name": "Unit", "id": "Unit"},
        {"name": "Description", "id": "Description"},
        {"name": "Formula Used", "id": "Formula"},
    ]
    if "Type" not in defs.columns:
        desc_cols = [c for c in desc_cols if c["id"] != "Type"]
    return dash_table.DataTable(
        columns=desc_cols,
        data=defs.to_dict("records"),
        style_cell={**TABLE_STYLE_CELL, "textAlign": "left", "whiteSpace": "normal", "height": "auto"},
        style_header=TABLE_STYLE_HEADER,
        style_data=TABLE_STYLE_DATA,
        page_size=15,
        style_table={"overflowX": "auto", "maxHeight": "60vh", "overflowY": "auto"},
    )


def _empty_figure(message: str) -> go.Figure:
    fig = go.Figure()
    fig.update_layout(**{k: v for k, v in _PLOT_PLACEHOLDER["layout"].items() if k != "title"})
    fig.update_layout(title={"text": message, "font": {"size": 14, "color": COLORS["muted"]}})
    return fig


dash_app.index_string = f"""<!DOCTYPE html>
<html>
    <head>
        {{%metas%}}
        <title>{{%title%}}</title>
        {{%favicon%}}
        {{%css%}}
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
        <style>
            body {{ margin: 0; background: {COLORS["bg"]}; color: {COLORS["text"]}; }}
            .dash-table-tooltip {{ background: {COLORS["surface"]} !important; }}
            .Select-control,
            .Select-menu-outer,
            .Select-menu,
            .VirtualizedSelectOption {{
                background-color: {COLORS["surface_alt"]} !important;
                border-color: {COLORS["border"]} !important;
                color: {COLORS["text"]} !important;
            }}
            .Select-value-label,
            .Select-placeholder,
            .Select-input > input {{
                color: {COLORS["text"]} !important;
            }}
            .VirtualizedSelectFocusedOption {{
                background-color: {COLORS["header_bg"]} !important;
                color: {COLORS["text"]} !important;
            }}
            .Select-option.is-focused,
            .Select-option.is-selected {{
                background-color: {COLORS["header_bg"]} !important;
                color: {COLORS["accent"]} !important;
            }}
            .dash-dropdown .Select-arrow-zone,
            .Select-arrow {{
                color: {COLORS["muted"]} !important;
            }}
            label {{ color: {COLORS["text"]}; }}
            .tab, .tab--selected {{
                color: {COLORS["text"]} !important;
                background-color: {COLORS["surface"]} !important;
                border-color: {COLORS["border"]} !important;
            }}
            .tab--selected {{
                border-top: 3px solid {COLORS["accent"]} !important;
                font-weight: 600;
            }}
            .dash-table-container .dash-spreadsheet th {{
                white-space: nowrap !important;
                vertical-align: middle;
            }}
            .dash-table-container .row {{
                flex-wrap: nowrap !important;
            }}
            #kpi-defs-backdrop {{
                position: fixed;
                inset: 0;
                background: rgba(0,0,0,0.55);
                z-index: 1000;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 1.5rem;
            }}
            #kpi-defs-dialog {{
                background: {COLORS["surface"]};
                border: 1px solid {COLORS["border"]};
                border-radius: 12px;
                max-width: 960px;
                width: 100%;
                max-height: 85vh;
                overflow: auto;
                padding: 1.25rem;
                box-shadow: 0 20px 50px rgba(0,0,0,0.45);
            }}
        </style>
    </head>
    <body>{{%app_entry%}}
        <footer>{{%config%}}{{%scripts%}}{{%renderer%}}</footer>
    </body>
</html>
"""

dash_app.layout = html.Div(
    [
        html.H1("KPIHub · Weekly KPI", style={"marginTop": 0, "fontWeight": 700}),
        html.P(
            "Weekly_KPI view with the same layout as the weekly Excel export. Pick one or two KPIs in the chart controls to plot by week number.",
            style={"color": COLORS["muted"], "marginBottom": "1rem"},
        ),
        html.Div(
            id="startup-error",
            children=_startup_error or "",
            style={
                "color": "#f87171",
                "marginBottom": "1rem",
                "display": "block" if _startup_error else "none",
            },
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.Label("Customer", style={"fontWeight": 600}),
                        dcc.Dropdown(
                            id="customer",
                            options=_customer_options,
                            value=_default_customer,
                            clearable=False,
                            style=DROPDOWN_STYLE,
                            className="dash-dropdown",
                        ),
                    ],
                    style={"flex": "1", "minWidth": "220px"},
                ),
                html.Div(
                    [
                        html.Label("Year", style={"fontWeight": 600}),
                        dcc.Dropdown(
                            id="year",
                            options=[{"label": str(y), "value": y} for y in range(_default_year - 2, _default_year + 2)],
                            value=_default_year,
                            clearable=False,
                            style=DROPDOWN_STYLE,
                            className="dash-dropdown",
                        ),
                    ],
                    style={"width": "120px"},
                ),
                html.Div(
                    [
                        html.Label("Region", style={"fontWeight": 600}),
                        dcc.Dropdown(
                            id="region",
                            clearable=False,
                            style=DROPDOWN_STYLE,
                            className="dash-dropdown",
                        ),
                    ],
                    style={"flex": "1", "minWidth": "200px"},
                ),
                html.Div(
                    html.Button(
                        "KPI definitions",
                        id="btn-kpi-defs",
                        n_clicks=0,
                        style={
                            "marginTop": "1.35rem",
                            "padding": "0.5rem 1rem",
                            "background": COLORS["surface_alt"],
                            "color": COLORS["text"],
                            "border": f"1px solid {COLORS['border']}",
                            "borderRadius": "8px",
                            "cursor": "pointer",
                            "fontWeight": 600,
                        },
                    ),
                ),
            ],
            style={"display": "flex", "flexWrap": "wrap", "gap": "1rem", "marginBottom": "1rem", "alignItems": "flex-start"},
        ),
        html.Div(id="sheet-title", style={"fontWeight": 600, "marginBottom": "0.75rem"}),
        html.Div(id="kpi-table", style=CARD_STYLE),
        html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                html.Label("Series A", style={"fontWeight": 600, "marginBottom": "0.35rem"}),
                                dcc.Dropdown(
                                    id="plot-series-a",
                                    options=[],
                                    value=None,
                                    clearable=True,
                                    placeholder="Select a KPI…",
                                    style=DROPDOWN_STYLE,
                                    className="dash-dropdown",
                                ),
                            ],
                            style={"flex": 1, "minWidth": "220px"},
                        ),
                        html.Div(
                            [
                                html.Label("Series B", style={"fontWeight": 600, "marginBottom": "0.35rem"}),
                                dcc.Dropdown(
                                    id="plot-series-b",
                                    options=[],
                                    value=None,
                                    clearable=True,
                                    placeholder="Select a KPI (optional)…",
                                    style=DROPDOWN_STYLE,
                                    className="dash-dropdown",
                                ),
                            ],
                            style={"flex": 1, "minWidth": "220px"},
                        ),
                    ],
                    style={"display": "flex", "flexWrap": "wrap", "gap": "1rem", "marginBottom": "1rem"},
                ),
                dcc.Graph(
                    id="kpi-plot",
                    figure=_empty_figure("Choose one or two KPIs to plot"),
                    config={"displayModeBar": True},
                ),
            ],
            style={**CARD_STYLE, "marginBottom": "1rem"},
        ),
        dcc.Store(id="plot-data"),
        html.Div(
            id="kpi-defs-backdrop",
            style={"display": "none"},
            children=[
                html.Div(
                    id="kpi-defs-dialog",
                    children=[
                        html.Div(
                            [
                                html.H3("KPI definitions", style={"margin": 0, "fontSize": "1.1rem"}),
                                html.Button(
                                    "Close",
                                    id="btn-kpi-defs-close",
                                    n_clicks=0,
                                    style={
                                        "padding": "0.35rem 0.85rem",
                                        "background": "transparent",
                                        "color": COLORS["accent"],
                                        "border": f"1px solid {COLORS['border']}",
                                        "borderRadius": "6px",
                                        "cursor": "pointer",
                                    },
                                ),
                            ],
                            style={
                                "display": "flex",
                                "justifyContent": "space-between",
                                "alignItems": "center",
                                "marginBottom": "1rem",
                            },
                        ),
                        html.Div(
                            id="kpi-definitions-content",
                            children=_definitions_table() if _db_ok else "",
                        ),
                    ],
                ),
            ],
        ),
    ],
    style=PAGE_STYLE,
)


@dash_app.callback(
    Output("region", "options"),
    Output("region", "value"),
    Input("customer", "value"),
    Input("year", "value"),
)
def update_regions(customer, year):
    if not customer or not _db_ok:
        return [], None
    regions = distinct_regions(customer)
    options = [
        {
            "label": region_label(r),
            "value": "__global__" if r is None or (isinstance(r, float) and pd.isna(r)) else r,
        }
        for r in regions
    ]
    if not options:
        options = [{"label": "Global", "value": "__global__"}]
    return options, options[0]["value"]


@dash_app.callback(
    Output("kpi-defs-backdrop", "style"),
    Input("btn-kpi-defs", "n_clicks"),
    Input("btn-kpi-defs-close", "n_clicks"),
    State("kpi-defs-backdrop", "style"),
    prevent_initial_call=True,
)
def toggle_defs_modal(open_clicks, close_clicks, current_style):
    style = dict(current_style or {})
    triggered = dash.ctx.triggered_id
    if triggered == "btn-kpi-defs":
        style["display"] = "flex"
    elif triggered == "btn-kpi-defs-close":
        style["display"] = "none"
    return style


@dash_app.callback(
    Output("sheet-title", "children"),
    Output("kpi-table", "children"),
    Output("plot-data", "data"),
    Input("customer", "value"),
    Input("year", "value"),
    Input("region", "value"),
)
def update_table(customer, year, region_value):
    if not customer or year is None or region_value is None or not _db_ok:
        return "", html.P("Select customer, year, and region.", style={"color": COLORS["muted"]}), None

    region = None if region_value == "__global__" else region_value
    try:
        sheets = build_excel_sheets_by_type(customer, int(year), region)
    except Exception as exc:  # noqa: BLE001
        return "", html.P(f"Query error: {exc}", style={"color": "#f87171"}), None

    title = f"KPI {region_label(region) if region else 'Global'} · {year} · Weekly (by Type)"
    store = _plot_store_payload(sheets)

    table_wrap = dcc.Tabs(
        [
            dcc.Tab(
                label=f"{kpi_type} ({len([c for c in display.columns if c not in META_COLS])} KPIs)",
                value=kpi_type,
                children=html.Div(
                    _excel_data_table(display, units, table_id={"type": "kpi-datatable", "index": kpi_type}),
                    style={"paddingTop": "0.75rem"},
                ),
                className="tab",
                selected_className="tab--selected",
            )
            for kpi_type, (display, units, _) in sheets.items()
        ],
        id="kpi-type-tabs",
        value=list(sheets.keys())[0],
        colors={
            "border": COLORS["border"],
            "primary": COLORS["accent"],
            "background": COLORS["surface"],
        },
    )

    return title, table_wrap, store


_PLOT_TRACE_COLORS = (COLORS["accent"], "#34d399")


def _kpi_plot_options(sheet_key: str | None, plot_data: dict | None) -> list[dict]:
    if not plot_data or not sheet_key or sheet_key not in plot_data:
        return []
    block = plot_data[sheet_key]
    records = block.get("records") or []
    units = block.get("units") or {}
    if not records:
        return []
    kpi_cols = [c for c in records[0] if c not in META_COLS]
    return [{"label": _header_label(c, units), "value": c} for c in kpi_cols]


def _figure_for_series(
    col_a: str | None,
    col_b: str | None,
    sheet_key: str | None,
    plot_data: dict | None,
) -> go.Figure:
    if not plot_data or not sheet_key or sheet_key not in plot_data:
        return _empty_figure("Choose one or two KPIs to plot")

    series: list[str] = []
    for c in (col_a, col_b):
        if c and c not in META_COLS and c not in series:
            series.append(c)
    if not series:
        return _empty_figure("Choose one or two KPIs to plot")

    block = plot_data[sheet_key]
    records = block.get("records") or []
    units = block.get("units") or {}
    if not records:
        return _empty_figure("No weekly data for this sheet.")

    weeks = [r.get("PeriodValue") for r in records]
    two_series = len(series) == 2 and series[0] != series[1]

    fig = go.Figure()
    for i, col in enumerate(series):
        if col not in records[0]:
            continue
        y_vals = [r.get(col, 0) for r in records]
        color = _PLOT_TRACE_COLORS[i % len(_PLOT_TRACE_COLORS)]
        yaxis = "y2" if two_series and i == 1 else "y"
        fig.add_trace(
            go.Bar(
                x=weeks,
                y=y_vals,
                name=_header_label(col, units),
                marker={"color": color, "line": {"color": COLORS["border"], "width": 1}},
                offsetgroup=str(i),
                yaxis=yaxis,
                hovertemplate="Week %{x}<br>%{y:.4g}<extra></extra>",
            )
        )

    if not fig.data:
        return _empty_figure("Selected KPIs are not available on this tab.")

    unit_a = (units.get(series[0]) or "").strip() or "Value"
    layout_kw = dict(
        paper_bgcolor=COLORS["surface"],
        plot_bgcolor=COLORS["surface_alt"],
        font={"color": COLORS["text"], "family": "Inter, Segoe UI, system-ui, sans-serif"},
        margin={"l": 56, "r": 56 if two_series else 24, "t": 48, "b": 48},
        xaxis={
            "title": "Week number (PeriodValue)",
            "dtick": 1,
            "gridcolor": COLORS["border"],
            "linecolor": COLORS["border"],
        },
        yaxis={
            "title": unit_a,
            "gridcolor": COLORS["border"],
            "linecolor": COLORS["border"],
        },
        barmode="group",
        bargap=0.15,
        bargroupgap=0.08,
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "x": 0},
        hovermode="x unified",
        title={
            "text": " · ".join(_header_label(c, units) for c in series),
            "font": {"size": 15, "color": COLORS["text"]},
        },
    )
    if two_series:
        unit_b = (units.get(series[1]) or "").strip() or "Value"
        layout_kw["yaxis2"] = {
            "title": unit_b,
            "overlaying": "y",
            "side": "right",
            "gridcolor": COLORS["border"],
            "linecolor": COLORS["border"],
        }
    elif len(series) == 1:
        layout_kw["showlegend"] = False

    fig.update_layout(**layout_kw)
    return fig


@dash_app.callback(
    Output("plot-series-a", "options"),
    Output("plot-series-b", "options"),
    Output("plot-series-a", "value"),
    Output("plot-series-b", "value"),
    Input("plot-data", "data"),
    Input("kpi-type-tabs", "value"),
)
def sync_plot_dropdowns(plot_data, sheet_key):
    options = _kpi_plot_options(sheet_key, plot_data)
    return options, options, None, None


@dash_app.callback(
    Output("kpi-plot", "figure"),
    Input("plot-series-a", "value"),
    Input("plot-series-b", "value"),
    Input("kpi-type-tabs", "value"),
    State("plot-data", "data"),
)
def update_kpi_plot(col_a, col_b, sheet_key, plot_data):
    return _figure_for_series(col_a, col_b, sheet_key, plot_data)


if __name__ == "__main__":
    dash_app.run(host="0.0.0.0", port=PORT, debug=False)