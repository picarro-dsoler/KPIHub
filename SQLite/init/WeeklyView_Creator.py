import os
import sys
import sqlite3

directory = os.path.abspath(os.path.dirname(__file__))
_root = os.path.abspath(os.path.join(directory, ".."))

# Add KPIHub root to sys.path so `lib.*` imports resolve regardless of cwd.
sys.path.insert(0, _root)
os.chdir(_root)

from lib.config import DB_PATH

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
    "InstatanoeusEmission",
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

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("DROP VIEW IF EXISTS Weekly_KPI;")
conn.commit()

query = """
CREATE VIEW IF NOT EXISTS Weekly_KPI AS
SELECT
    kd.Year,
    kd.PeriodValue,
    kc.Name AS CustomerName,
    kd.BoundaryRegion,
    """ + ",\n    ".join(
    [f"SUM(CASE WHEN kd.KPIId = '{kpi}' THEN kd.Value END) AS [{kpi}]" for kpi in KPI_META_KEYS]
) + """
FROM KPI_Data kd
LEFT JOIN KPI_Customer kc ON kd.CustomerId = kc.CustomerId
WHERE kd.PeriodType = 'Week'
GROUP BY kd.Year, kd.PeriodValue, kd.CustomerId, kc.Name, kd.BoundaryRegion;"""

cursor.execute(query)
conn.commit()
conn.close()
