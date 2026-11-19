import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from bootstrap_paths import activate

activate()

KPI_META_KEYS = [
    "ReportAssetLengthKm",
    "AssetCoveredLengthKm",
    "DistributionPipeKm",
    "DistributionPipeCoveredKm",
    "CumulativeAssetCoveredLengthKm",
    "ServicePipeKm",
    "ServicePipeCoveredKm",
    "ReportCount",
    "DaysCount",
    "FOVMain",
    "SurveyDurationHours",
    "TargetDurationHours",
    "CustomerUtilization",
    "StarndardUtilization",
    "TotalSurveyors",
    "ProductivityPerSurveyor",
    "SurveyCount",
    "AvgSpeedKm",
    "SurveysCarDay",
    "IdleTime",
    "TotalDrivenLengthKm",
    "DrivingRatio",
    "NightDrivenLength",
    "DayDrivenLength",
    "NightRatio",
    "DayRatio",
    "PeakAboveSATCount",
    "LisaCount",
    "EmissionRate",
    "B0Count",
    "B1Count",
    "Bm1Count",
    "Bm2Count",
    "NGCount",
    "PGCount",
    "Not_NGCount",
    "LisaDensity",
    "InstantanoeusEmission",
    "B0Density",
    "B1Density",
    "Bm1Density",
    "Bm2Density",
    "B0Share",
    "B1Share",
    "Bm1Share",
    "Bm2Share",
    "NGShare",
    "PGShare",
    "Not_NGShare",
    "POR",
    "CurrentCompletion",
]

from lib.config import KPIHUB_CONNECTION
from lib.KPIHubConnection import PostgreSQLConnection
from locallib.query import Query

conn = KPIHUB_CONNECTION
is_pg = isinstance(conn, PostgreSQLConnection)

if is_pg:
    pivot = [
        f"SUM(CASE WHEN kd.KPIId = '{kpi}' THEN kd.Value::double precision END) AS {kpi}"
        for kpi in KPI_META_KEYS
    ]
    drop_sql = "DROP VIEW IF EXISTS Weekly_KPI;"
    pivot_sql = ",\n    ".join(pivot)
    create_sql = f"""
CREATE VIEW Weekly_KPI AS
SELECT
    kd.Year,
    kd.PeriodValue,
    kc.Name AS CustomerName,
    kd.BoundaryRegion,
    {pivot_sql}
FROM KPI_Data kd
LEFT JOIN KPI_Customer kc ON kd.CustomerId = kc.CustomerId
WHERE kd.PeriodType::text = 'Week'
GROUP BY kd.Year, kd.PeriodValue, kd.CustomerId, kc.Name, kd.BoundaryRegion;
"""
    Query(drop_sql).execute(conn, return_df=False)
    Query(create_sql).execute(conn, return_df=False)
else:
    pivot = [
        f"SUM(CASE WHEN kd.KPIId = '{kpi}' THEN kd.Value END) AS [{kpi}]"
        for kpi in KPI_META_KEYS
    ]
    pivot_sql = ",\n    ".join(pivot)
    query = f"""
CREATE VIEW IF NOT EXISTS Weekly_KPI AS
SELECT
    kd.Year,
    kd.PeriodValue,
    kc.Name AS CustomerName,
    kd.BoundaryRegion,
    {pivot_sql}
FROM KPI_Data kd
LEFT JOIN KPI_Customer kc ON kd.CustomerId = kc.CustomerId
WHERE kd.PeriodType = 'Week'
GROUP BY kd.Year, kd.PeriodValue, kd.CustomerId, kc.Name, kd.BoundaryRegion;"""
    db = conn.engine
    cursor = db.cursor()
    cursor.execute("DROP VIEW IF EXISTS Weekly_KPI;")
    cursor.execute(query)
    db.commit()
    cursor.close()
