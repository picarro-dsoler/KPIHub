COLORS = {
    "bg": "#0b1220",
    "surface": "#131c2e",
    "surface_alt": "#1a2740",
    "border": "#2a3a52",
    "text": "#e8eef7",
    "muted": "#94a3b8",
    "accent": "#38bdf8",
    "header_bg": "#1e293b",
    "unit_row_bg": "#0f172a",
}

PAGE_STYLE = {
    "minHeight": "100vh",
    "backgroundColor": COLORS["bg"],
    "color": COLORS["text"],
    "fontFamily": "'Inter', 'Segoe UI', system-ui, sans-serif",
    "padding": "1.5rem 2rem",
}

CARD_STYLE = {
    "backgroundColor": COLORS["surface"],
    "border": f"1px solid {COLORS['border']}",
    "borderRadius": "12px",
    "padding": "1.25rem",
    "marginBottom": "1rem",
}

TABLE_STYLE_HEADER = {
    "backgroundColor": COLORS["header_bg"],
    "fontWeight": "700",
    "textAlign": "center",
    "border": f"1px solid {COLORS['border']}",
    "padding": "8px 10px",
    "whiteSpace": "nowrap",
    "height": "auto",
    "lineHeight": "1.3",
    "verticalAlign": "middle",
}

TABLE_STYLE_FILTER = {
    "backgroundColor": COLORS["unit_row_bg"],
    "fontWeight": "700",
    "textAlign": "center",
    "borderBottom": "2px solid #000",
    "border": f"1px solid {COLORS['border']}",
    "padding": "6px",
}

TABLE_STYLE_CELL = {
    "textAlign": "center",
    "padding": "6px 10px",
    "border": f"1px solid {COLORS['border']}",
    "fontVariantNumeric": "tabular-nums",
    "whiteSpace": "nowrap",
    "minWidth": "96px",
}

TABLE_STYLE_DATA = {
    "backgroundColor": COLORS["surface_alt"],
    "color": COLORS["text"],
}

DROPDOWN_STYLE = {
    "backgroundColor": COLORS["surface_alt"],
    "color": COLORS["text"],
    "borderColor": COLORS["border"],
}