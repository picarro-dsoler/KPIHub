import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from bootstrap_paths import activate

activate()

from lib.config import KPIHUB_CONNECTION
from lib.KPIHubConnection import PostgreSQLConnection
from locallib.query import Query
from lib.views.ViewConfig import *

conn = KPIHUB_CONNECTION
for kpi_view in KPI_CUSTOMER_VIEWS:
    is_pg = isinstance(conn, PostgreSQLConnection)
    if is_pg:
        pivot = [
            f"SUM(CASE WHEN kd.KPIId = '{kpi_name}' THEN kd.Value::double precision END) AS {kpi_name}"
            for kpi_name in kpi_view["Columns"].keys()
        ]
        drop_sql = f"DROP VIEW IF EXISTS {kpi_view['Name']};"
        pivot_sql = ",\n    ".join(pivot)
        create_sql = f"""
    CREATE VIEW {kpi_view['Name']} AS
    SELECT
        kd.Year,
        kd.PeriodValue,
        kc.Name AS CustomerName,
        kd.BoundaryRegion,
        {pivot_sql}
    FROM KPI_Data kd
    LEFT JOIN KPI_Customer kc ON kd.CustomerId = kc.CustomerId
    WHERE kd.PeriodType::text = '{kpi_view["PeriodType"]}'
    GROUP BY kd.Year, kd.PeriodValue, kd.CustomerId, kc.Name, kd.BoundaryRegion;
    """
        Query(drop_sql).execute(conn, return_df=False)
        Query(create_sql).execute(conn, return_df=False)
    else:
        pivot = [
            f"SUM(CASE WHEN kd.KPIId = '{kpi_name}' THEN kd.Value END) AS [{kpi_name}]"
            for kpi_name in kpi_view["Columns"].keys()
        ]
        pivot_sql = ",\n    ".join(pivot)
        query = f"""
    CREATE VIEW IF NOT EXISTS {kpi_view['Name']} AS
    SELECT
        kd.Year,
        kd.PeriodValue,
        kc.Name AS CustomerName,
        kd.BoundaryRegion,
        {pivot_sql}
    FROM KPI_Data kd
    LEFT JOIN KPI_Customer kc ON kd.CustomerId = kc.CustomerId
    WHERE kd.PeriodType = '{kpi_view["PeriodType"]}'
    GROUP BY kd.Year, kd.PeriodValue, kd.CustomerId, kc.Name, kd.BoundaryRegion;"""
        db = conn.engine
        cursor = db.cursor()
        cursor.execute(f"DROP VIEW IF EXISTS {kpi_view['Name']};")
        cursor.execute(query)
        db.commit()
        cursor.close()
