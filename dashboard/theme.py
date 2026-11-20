# Palette aligned with picarro.com (daudo_subtheme): brand green, dark bands, grey copy.
# Sources: .btn-theme / .btn-theme-submit (#6eb43f), dark blocks (#111111), borders (#454545),
# secondary text (#788592, #a7a7a7).
COLORS = {
    "bg": "#111111",
    "surface": "#1c1c1c",
    "surface_alt": "#232323",
    "border": "#454545",
    "text": "#ffffff",
    "muted": "#788592",
    "accent": "#6eb43f",
    "accent_light": "#7aba7b",
    "accent_dark": "#5a9a33",
    "header_bg": "#0b0b0b",
    "unit_row_bg": "#181818",
}

PAGE_STYLE = {
    "minHeight": "100vh",
    "backgroundColor": COLORS["bg"],
    "color": COLORS["text"],
    "fontFamily": "Helvetica, 'Helvetica Neue', Arial, sans-serif",
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
    "borderBottom": f"2px solid {COLORS['accent']}",
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