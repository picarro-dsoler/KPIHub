"""Print all table definitions from IngesterTables.py into a PDF."""
import os
import sys
from datetime import datetime

directory = os.path.abspath(os.path.dirname(__file__))
_root = os.path.abspath(os.path.join(directory, "..", ".."))
sys.path.insert(0, _root)

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from lib.tables.IngesterTables import *
from lib.tables.KPITable import KPITable

OUTPUT_PDF = os.path.join(directory, "IngesterTables.pdf")


def iter_tables():
    """Yield all KPITable instances defined in IngesterTables."""
    import lib.tables.IngesterTables as mod

    for name in sorted(dir(mod)):
        obj = getattr(mod, name)
        if isinstance(obj, KPITable):
            yield obj


def column_key(column):
    key = getattr(column, "key", None)
    return "" if key is None else str(key)


def build_pdf(output_path=OUTPUT_PDF):
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleCustom",
        parent=styles["Heading1"],
        fontSize=18,
        spaceAfter=12,
    )
    table_title_style = ParagraphStyle(
        "TableTitle",
        parent=styles["Heading2"],
        fontSize=13,
        spaceBefore=8,
        spaceAfter=6,
    )
    body_style = styles["Normal"]

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )
    story = []

    tables = list(iter_tables())
    story.append(Paragraph("KPIHub Ingester Tables", title_style))
    story.append(
        Paragraph(
            f"Generated from <b>lib/tables/IngesterTables.py</b> on {datetime.now():%Y-%m-%d %H:%M}",
            body_style,
        )
    )
    story.append(Paragraph(f"Total tables: <b>{len(tables)}</b>", body_style))
    story.append(Spacer(1, 0.4 * cm))

    # Index (kept together so it does not split mid-page)
    index_data = [["#", "Table", "Columns"]]
    for i, table in enumerate(tables, start=1):
        index_data.append([str(i), table.name, str(len(table.columns))])
    index = Table(index_data, colWidths=[1.2 * cm, 10 * cm, 3 * cm])
    index.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e79")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eef3f8")]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    index.splitByRow = 0
    story.append(
        KeepTogether(
            [
                Paragraph("Index", table_title_style),
                index,
            ]
        )
    )
    story.append(PageBreak())

    for table in tables:
        data = [["#", "Column", "Datatype", "Key"]]
        for i, column in enumerate(table.columns, start=1):
            data.append(
                [
                    str(i),
                    column.name,
                    str(getattr(column, "datatype", "") or ""),
                    column_key(column),
                ]
            )

        col_table = Table(data, colWidths=[1.2 * cm, 7.5 * cm, 4.5 * cm, 2.5 * cm])
        col_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2e75b6")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.HexColor("#f5f5f5")],
                    ),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ]
            )
        )
        # Do not split this table across pages; move whole block to next page if needed
        col_table.splitByRow = 0
        story.append(
            KeepTogether(
                [
                    Paragraph(table.name, table_title_style),
                    Paragraph(f"Columns: <b>{len(table.columns)}</b>", body_style),
                    Spacer(1, 0.2 * cm),
                    col_table,
                    Spacer(1, 0.6 * cm),
                ]
            )
        )

    doc.build(story)
    return output_path


if __name__ == "__main__":
    path = build_pdf()
    print(f"Wrote {path}")
