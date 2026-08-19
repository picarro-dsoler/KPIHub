"""
Generate KPIHub documentation PDF:
  - Table schemas and descriptions (from lib/tables/IngesterTables.py)
  - Ingestion pipeline diagrams (from lib/ingester/*.py)
  - KPI calculation flow diagrams (from lib/kpi_processor/KPIReport.py)

Run from KPIHub/SQLite:
    python docs/GenerateKPIHubDocumentation.py
"""
from __future__ import annotations

import os
import sys
from datetime import datetime
from textwrap import fill

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

DOCS_DIR = os.path.abspath(os.path.dirname(__file__))
SQLITE_ROOT = os.path.abspath(os.path.join(DOCS_DIR, ".."))
sys.path.insert(0, SQLITE_ROOT)

from lib.tables.IngesterTables import *  # noqa: E402, F403
from lib.tables.KPITable import KPITable  # noqa: E402

OUTPUT_PDF = os.path.join(DOCS_DIR, "KPIHub_Documentation.pdf")
DIAGRAMS_DIR = os.path.join(DOCS_DIR, "diagrams")

# ---------------------------------------------------------------------------
# Table metadata (human-readable descriptions)
# ---------------------------------------------------------------------------
TABLE_DESCRIPTIONS: dict[str, str] = {
    "KPI_Customer": (
        "Master list of customers tracked in KPIHub. Links each customer to their "
        "LSDB location (EU1/EU2), country, and active status."
    ),
    "KPI_Country": "Country reference table used for regional KPI aggregation.",
    "KPI_POR": (
        "Plan of Record (POR) targets per customer and year. Defines contractual "
        "asset-coverage goals and date ranges used to compute completion KPIs."
    ),
    "KPI_OutputExcelLocation": (
        "Box folder IDs where Excel KPI outputs are uploaded per customer."
    ),
    "KPI_Utilization": (
        "Per-customer utilization parameters: working days/hours, sunrise/sunset "
        "hours, and base surveyor count. Used by KPISurveySummary."
    ),
    "KPI_ReportSummary": (
        "One row per final report. Ingested from LSDB (and DataHub for EU) with "
        "pipe lengths, coverage, boundary metadata, and report area geometry."
    ),
    "KPI_PeakSATLocation": (
        "Box file reference for the Peak-Above-SAT Excel workbook per customer."
    ),
    "KPI_PeakAboveSAT": (
        "Individual peaks above the SAT threshold, loaded from Box Excel files. "
        "Source for PeakAboveSATCount KPI."
    ),
    "KPI_EmissionSourceSummary": (
        "Per-report emission source aggregates: LISA counts, bin counts (B0/B1/B-1/B-2), "
        "emission rates (SCFH and SLPM), and disposition shares (NG/PG/Not-NG)."
    ),
    "KPI_SurveySummary": (
        "Per-survey-per-report segment statistics: duration, day/night km, idle/active "
        "time, speed, and segment weights after geo-intersection with report area."
    ),
    "KPI_Definition": (
        "KPI catalogue: name, unit, formula text, and description for each defined KPI."
    ),
    "KPI_Data": (
        "Computed KPI values (melted long format). One row per KPI × customer × "
        "period with Id, KPIId, Year, PeriodType, PeriodValue, and Value."
    ),
}

# Per-column descriptions keyed as "TableName.ColumnName"
COLUMN_DESCRIPTIONS: dict[str, str] = {
    # KPI_Customer
    "KPI_Customer.CustomerId": "Primary key — unique customer identifier (GUID).",
    "KPI_Customer.Name": "Full customer name used for lookups and KPI output labels.",
    "KPI_Customer.ShortName": "Abbreviated customer name for display.",
    "KPI_Customer.Active": "Whether the customer is currently active (1/0).",
    "KPI_Customer.DBLocation": "LSDB connection key (e.g. EU1, EU2) for source queries.",
    "KPI_Customer.Country": "Country name; used for regional KPI aggregation.",
    "KPI_Customer.LastUpdated": "Timestamp of the last upsert to this record.",
    # KPI_Country
    "KPI_Country.CountryId": "Primary key — unique country identifier (GUID).",
    "KPI_Country.Name": "Country name.",
    "KPI_Country.LastUpdated": "Timestamp of the last upsert to this record.",
    # KPI_POR
    "KPI_POR.CustomerId": "Customer this POR target applies to.",
    "KPI_POR.Year": "Calendar year of the POR commitment.",
    "KPI_POR.StartingDate": "Start of the POR measurement period.",
    "KPI_POR.EndingDate": "End of the POR measurement period.",
    "KPI_POR.Description": "Free-text description of the POR target.",
    "KPI_POR.Value": "Target asset-coverage length (km) for completion KPIs.",
    "KPI_POR.Unit": "Unit of the POR value (typically km).",
    "KPI_POR.LastUpdated": "Timestamp of the last upsert to this record.",
    # KPI_OutputExcelLocation
    "KPI_OutputExcelLocation.CustomerId": "Primary key — customer receiving Excel outputs.",
    "KPI_OutputExcelLocation.BoxFolderId": "Box folder ID where KPI Excel files are uploaded.",
    "KPI_OutputExcelLocation.LastUpdated": "Timestamp of the last upsert to this record.",
    # KPI_Utilization
    "KPI_Utilization.CustomerId": "Primary key — customer these utilization params apply to.",
    "KPI_Utilization.WorkingDays": "Expected working days per week for utilization KPIs.",
    "KPI_Utilization.WorkingHours": "Expected working hours per day for utilization KPIs.",
    "KPI_Utilization.SunriseHour": "Hour (0–23) defining start of day shift for surveys.",
    "KPI_Utilization.SunsetHour": "Hour (0–23) defining start of night shift for surveys.",
    "KPI_Utilization.BaseSurveyorCount": "Baseline number of surveyor units for the customer.",
    "KPI_Utilization.Description": "Free-text notes on utilization assumptions.",
    "KPI_Utilization.LastUpdated": "Timestamp of the last upsert to this record.",
    # KPI_ReportSummary
    "KPI_ReportSummary.ReportId": "Primary key — unique report identifier from LSDB.",
    "KPI_ReportSummary.CustomerId": "Foreign key to KPI_Customer.",
    "KPI_ReportSummary.ReportName": "Report title from LSDB.",
    "KPI_ReportSummary.ReportDate": "Date the report was started or finalized.",
    "KPI_ReportSummary.ReportYear": "Calendar year derived from ReportDate.",
    "KPI_ReportSummary.ReportMonth": "Calendar month derived from ReportDate.",
    "KPI_ReportSummary.ReportWeek": "ISO week number derived from ReportDate.",
    "KPI_ReportSummary.ReportAssetLengthKm": "Total asset length (km) in the report boundary.",
    "KPI_ReportSummary.AssetCoveredLengthKm": "Asset length actually covered by surveys (km).",
    "KPI_ReportSummary.DistributionPipeKm": "Total distribution pipe length (km).",
    "KPI_ReportSummary.DistributionPipeCoveredKm": "Distribution pipe length covered (km); FOV denominator.",
    "KPI_ReportSummary.ServicePipeKm": "Total service pipe length (km).",
    "KPI_ReportSummary.ServicePipeCoveredKm": "Service pipe length covered (km).",
    "KPI_ReportSummary.BoundaryName": "Boundary name from DataHub (EU customers).",
    "KPI_ReportSummary.BoundaryType": "Boundary type classification from DataHub.",
    "KPI_ReportSummary.BoundaryMode": "Boundary mode from DataHub.",
    "KPI_ReportSummary.BoundaryPlant": "Plant name within the boundary hierarchy.",
    "KPI_ReportSummary.BoundarySubplant": "Sub-plant name within the boundary hierarchy.",
    "KPI_ReportSummary.BoundaryRegion": "Region name; used as KPI aggregation dimension.",
    "KPI_ReportSummary.BoundarySubRegion": "Sub-region within the boundary hierarchy.",
    "KPI_ReportSummary.ReportArea": "Report boundary polygon stored as WKT geometry text.",
    "KPI_ReportSummary.LastUpdated": "Timestamp of the last upsert to this record.",
    # KPI_PeakSATLocation
    "KPI_PeakSATLocation.CustomerId": "Primary key — customer owning the Peak SAT file.",
    "KPI_PeakSATLocation.BoxFileId": "Box file ID of the Peak-Above-SAT Excel workbook.",
    "KPI_PeakSATLocation.LastUpdated": "Timestamp of the last upsert to this record.",
    # KPI_PeakAboveSAT
    "KPI_PeakAboveSAT.CustomerId": "Foreign key to KPI_Customer.",
    "KPI_PeakAboveSAT.PeakName": "Name or label of the peak event.",
    "KPI_PeakAboveSAT.PeakId": "Primary key — unique peak identifier.",
    "KPI_PeakAboveSAT.Date": "Date the peak was detected.",
    "KPI_PeakAboveSAT.ReportYear": "Calendar year derived from Date.",
    "KPI_PeakAboveSAT.WeekNumber": "ISO week number derived from Date.",
    "KPI_PeakAboveSAT.Disposition": "Peak disposition classification.",
    "KPI_PeakAboveSAT.LocalTime": "Local timestamp of the peak detection.",
    "KPI_PeakAboveSAT.BoundaryName": "Boundary where the peak was detected.",
    "KPI_PeakAboveSAT.BoundaryRegion": "Region where the peak was detected.",
    "KPI_PeakAboveSAT.EmissionRate": "Measured emission rate at the peak (SCFH).",
    "KPI_PeakAboveSAT.PeakGpsLatitude": "GPS latitude of the peak location.",
    "KPI_PeakAboveSAT.PeakGpsLongitude": "GPS longitude of the peak location.",
    "KPI_PeakAboveSAT.Easting": "Projected easting coordinate.",
    "KPI_PeakAboveSAT.Northing": "Projected northing coordinate.",
    "KPI_PeakAboveSAT.UserName": "Operator who recorded the peak.",
    "KPI_PeakAboveSAT.SurveyorUnit": "Surveyor unit that detected the peak.",
    "KPI_PeakAboveSAT.AnalyzerSerialNumber": "Analyzer serial number used during detection.",
    "KPI_PeakAboveSAT.Hyperlink": "URL link to the peak record in the source system.",
    "KPI_PeakAboveSAT.LastUpdated": "Timestamp of the last upsert to this record.",
    # KPI_EmissionSourceSummary
    "KPI_EmissionSourceSummary.ReportId": "Primary key — one row per report.",
    "KPI_EmissionSourceSummary.EmissionRate": "Sum of emission rates (SCFH) for non-disposition-2 sources.",
    "KPI_EmissionSourceSummary.EmissionRateLPM": "EmissionRate converted to SLPM (× 0.471947).",
    "KPI_EmissionSourceSummary.RepresentativeEmissionRate": "Sum of representative emission rates (SCFH).",
    "KPI_EmissionSourceSummary.RepresentativeEmissionRateLPM": "Representative emission rate sum in SLPM.",
    "KPI_EmissionSourceSummary.LisaCount": "Count of LISA emission sources (Disposition ≠ 2).",
    "KPI_EmissionSourceSummary.LisaPSCount": "LISA count where IsFiltered = 0 and Disposition ≠ 2.",
    "KPI_EmissionSourceSummary.B0Count": "Count of sources in representative bin B0.",
    "KPI_EmissionSourceSummary.B1Count": "Count of sources in representative bin B1.",
    "KPI_EmissionSourceSummary.Bm1Count": "Count of sources in representative bin B-1.",
    "KPI_EmissionSourceSummary.Bm2Count": "Count of sources in representative bin B-2.",
    "KPI_EmissionSourceSummary.B0RepEmissionRateLPM": "B0 representative emission rate sum (SLPM).",
    "KPI_EmissionSourceSummary.B1RepEmissionRateLPM": "B1 representative emission rate sum (SLPM).",
    "KPI_EmissionSourceSummary.Bm1RepEmissionRateLPM": "B-1 representative emission rate sum (SLPM).",
    "KPI_EmissionSourceSummary.Bm2RepEmissionRateLPM": "B-2 representative emission rate sum (SLPM).",
    "KPI_EmissionSourceSummary.B0RepEmissionRate": "B0 representative emission rate sum (SCFH).",
    "KPI_EmissionSourceSummary.B1RepEmissionRate": "B1 representative emission rate sum (SCFH).",
    "KPI_EmissionSourceSummary.Bm1RepEmissionRate": "B-1 representative emission rate sum (SCFH).",
    "KPI_EmissionSourceSummary.Bm2RepEmissionRate": "B-2 representative emission rate sum (SCFH).",
    "KPI_EmissionSourceSummary.Not_NGCount": "Count of sources with Disposition = 2 (not natural gas).",
    "KPI_EmissionSourceSummary.PGCount": "Count of sources with Disposition = 3 (propane/biogas).",
    "KPI_EmissionSourceSummary.NGCount": "Count of sources with Disposition = 1 (natural gas).",
    "KPI_EmissionSourceSummary.LastUpdated": "Timestamp of the last upsert to this record.",
    # KPI_SurveySummary
    "KPI_SurveySummary.SurveyId": "Survey identifier from LSDB.",
    "KPI_SurveySummary.ReportId": "Report this survey segment data belongs to (composite key).",
    "KPI_SurveySummary.SurveyorUnit": "Identifier of the surveyor vehicle/unit.",
    "KPI_SurveySummary.SurveyDurationMinutes": "Weighted survey duration (raw duration × segment weight).",
    "KPI_SurveySummary.SurveyRawDurationMinutes": "Full survey duration in minutes (unweighted).",
    "KPI_SurveySummary.SegmentWeight": "Fraction of survey segments inside the report area.",
    "KPI_SurveySummary.StartHour": "Hour (0–23) when the survey started.",
    "KPI_SurveySummary.StartTime": "Time-of-day when the survey started.",
    "KPI_SurveySummary.StartEpoch": "Survey start as Unix epoch seconds.",
    "KPI_SurveySummary.EndTime": "Time-of-day when the survey ended.",
    "KPI_SurveySummary.EndEpoch": "Survey end as Unix epoch seconds.",
    "KPI_SurveySummary.StartDay": "Calendar date when the survey started.",
    "KPI_SurveySummary.EndDay": "Calendar date when the survey ended.",
    "KPI_SurveySummary.LateralRotation": "Lateral rotation setting during the survey.",
    "KPI_SurveySummary.NumberOfPeaks": "Number of peaks detected during the survey.",
    "KPI_SurveySummary.DaySegments": "Segments classified as day (between sunrise and sunset).",
    "KPI_SurveySummary.NightSegments": "Segments classified as night.",
    "KPI_SurveySummary.ActiveSegments": "Segments where vehicle speed ≥ speed threshold.",
    "KPI_SurveySummary.IdleSegments": "Segments where vehicle speed < speed threshold.",
    "KPI_SurveySummary.TotalSegments": "Total segments inside the report area for this survey.",
    "KPI_SurveySummary.TotalSegmentsInSurvey": "Total segments in the full survey (before clipping).",
    "KPI_SurveySummary.TotalKilometers": "Total distance driven inside report area (km).",
    "KPI_SurveySummary.DayKilometers": "Day-time distance driven inside report area (km).",
    "KPI_SurveySummary.NightKilometers": "Night-time distance driven inside report area (km).",
    "KPI_SurveySummary.IdleTimeMinutes": "Idle time inside report area (minutes).",
    "KPI_SurveySummary.ActiveTimeMinutes": "Active driving time inside report area (minutes).",
    "KPI_SurveySummary.SegmentDurationMinutes": "Total segment duration inside report area (minutes).",
    "KPI_SurveySummary.AvgSpeedKm": "Mean vehicle speed inside report area (km/h).",
    "KPI_SurveySummary.LastUpdated": "Timestamp of the last upsert to this record.",
    # KPI_Definition
    "KPI_Definition.Name": "Primary key — KPI identifier (e.g. FOVMain, LisaDensity).",
    "KPI_Definition.Unit": "Display unit for the KPI (%, km, count, etc.).",
    "KPI_Definition.Formula": "Human-readable formula text for the KPI.",
    "KPI_Definition.Description": "Long-form description of what the KPI measures.",
    "KPI_Definition.LastUpdated": "Timestamp of the last upsert to this record.",
    # KPI_Data
    "KPI_Data.Id": "Primary key — composite ID (KPIId + customer + period dimensions).",
    "KPI_Data.KPIId": "Name of the KPI (matches KPI_Definition.Name).",
    "KPI_Data.CustomerId": "Customer this KPI value belongs to.",
    "KPI_Data.BoundaryRegion": "Optional region dimension for regional KPI breakdowns.",
    "KPI_Data.Year": "Calendar year of the KPI period.",
    "KPI_Data.PeriodType": "Period granularity label (e.g. Week, Year).",
    "KPI_Data.PeriodValue": "Period number (e.g. ISO week number).",
    "KPI_Data.Value": "Computed KPI value stored as text/numeric string.",
    "KPI_Data.DataType": "Optional data-type tag for the value.",
    "KPI_Data.LastUpdated": "Timestamp of the last upsert to this record.",
}


def get_column_description(table_name: str, column_name: str) -> str:
    return COLUMN_DESCRIPTIONS.get(
        f"{table_name}.{column_name}",
        f"Column {column_name} on {table_name}.",
    )

# ---------------------------------------------------------------------------
# KPI calculation definitions (parsed from KPIReport.py)
# ---------------------------------------------------------------------------
KPI_PROCESSORS = {
    "KPIPOR": {
        "title": "KPIPOR — Plan of Record Completion",
        "source_tables": ["KPI_ReportSummary", "KPI_POR"],
        "group_by": ["ReportYear", "ReportWeek"],
        "outputs": {
            "CumulativeAssetCoveredLengthKm": (
                "Running sum of AssetCoveredLengthKm within each ReportYear "
                "(cumulative week over week)"
            ),
            "POR": "POR target value for the week (from KPI_POR date ranges)",
            "CurrentCompletion": (
                "100 × CumulativeAssetCoveredLengthKm / POR  (%)"
            ),
        },
        "notes": (
            "Reports are filtered to those whose ReportDate falls within any "
            "KPI_POR StartingDate–EndingDate window."
        ),
    },
    "KPIPeakSAT": {
        "title": "KPIPeakSAT — Peaks Above SAT",
        "source_tables": ["KPI_PeakAboveSAT"],
        "group_by": ["ReportYear", "WeekNumber"],
        "outputs": {
            "PeakAboveSATCount": "COUNT(PeakId) per group",
        },
        "notes": "Data ingested from Box Excel via PeakSATIngester.",
    },
    "KPIReport": {
        "title": "KPIReport — Report Coverage & Lengths",
        "source_tables": ["KPI_ReportSummary"],
        "group_by": ["ReportYear", "ReportWeek"],
        "outputs": {
            "FOVMain": (
                "100 × SUM(DistributionPipeCoveredKm) / SUM(DistributionPipeKm)"
            ),
            "ReportAssetLengthKm": "SUM(ReportAssetLengthKm)",
            "AssetCoveredLengthKm": "SUM(AssetCoveredLengthKm)",
            "DistributionPipeKm": "SUM(DistributionPipeKm)",
            "DistributionPipeCoveredKm": "SUM(DistributionPipeCoveredKm)",
            "ServicePipeKm": "SUM(ServicePipeKm)",
            "ServicePipeCoveredKm": "SUM(ServicePipeCoveredKm)",
            "ReportCount": "COUNT(rows)",
        },
        "notes": "Field of View (FOV) main metric is distribution pipe coverage percentage.",
    },
    "KPIEmissionSource": {
        "title": "KPIEmissionSource — Emission & LISA Metrics",
        "source_tables": ["KPI_ReportSummary", "KPI_EmissionSourceSummary"],
        "group_by": ["ReportYear", "ReportWeek"],
        "denominator": "SUM(DistributionPipeCoveredKm)",
        "outputs": {
            "LisaCount": "SUM(LisaCount)",
            "EmissionRate": "SUM(EmissionRate)",
            "B0Count … Bm2Count": "SUM of each bin count",
            "NGCount, PGCount, Not_NGCount": "SUM of disposition counts",
            "EmissionRateLPM": "SUM(EmissionRateLPM)",
            "RepresentativeEmissionRate(LPM)": "SUM of representative rates",
            "B0RepEmissionRate(LPM) … Bm2RepEmissionRate(LPM)": "SUM per bin",
            "LisaDensity": "LisaCount / DistributionPipeCoveredKm",
            "InstatanoeusEmission": "EmissionRate / DistributionPipeCoveredKm",
            "InstatanoeusEmissionLPM": "EmissionRateLPM / DistributionPipeCoveredKm",
            "InstatanoeusRepEmission(LPM)": "Representative rate / denominator",
            "B0Density … Bm2Density": "Bin count / DistributionPipeCoveredKm",
            "NGDensity, PGDensity": "Disposition count / denominator",
            "B0Share … Bm2Share": "100 × bin count / LisaCount",
            "NGShare, PGShare, Not_NGShare": (
                "100 × disposition count / (NG + PG + Not_NG)"
            ),
        },
        "notes": (
            "KPI_ReportSummary and KPI_EmissionSourceSummary are joined on ReportId. "
            "Density metrics use DistributionPipeCoveredKm as denominator."
        ),
    },
    "KPISurveySummary": {
        "title": "KPISurveySummary — Survey Utilization & Driving",
        "source_tables": ["KPI_ReportSummary", "KPI_SurveySummary", "KPI_Utilization"],
        "group_by": ["ReportYear", "ReportWeek"],
        "outputs": {
            "SurveyDurationHours": "SUM(SurveyDurationMinutes) / 60",
            "StarndardUtilization": (
                "100 × SurveyDurationHours / (6 × 5 × TotalSurveyors)"
            ),
            "TotalSurveyors": "COUNT(DISTINCT SurveyorUnit)",
            "ProductivityPerSurveyor": (
                "SUM(DistributionPipeCoveredKm from unique reports) / TotalSurveyors"
            ),
            "SurveyCount": "COUNT(DISTINCT SurveyId)",
            "AvgSpeedKm": (
                "SUM(AvgSpeedKm × TotalSegments) / SUM(TotalSegments)"
            ),
            "IdleTime": (
                "100 × SUM(IdleTimeMinutes) / SUM(SurveyDurationMinutes)"
            ),
            "TotalDrivenLengthKm": "SUM(TotalKilometers)",
            "DrivingRatio": (
                "SUM(TotalKilometers) / SUM(AssetCoveredLengthKm from unique reports)"
            ),
            "NightDrivenLength / DayDrivenLength": "SUM of night/day km",
            "NightRatio / DayRatio": "100 × night(or day) km / TotalKilometers",
            "TargetDurationHours": (
                "DaysCount × WorkingHours × TotalSurveyors  (weekly only)"
            ),
            "CustomerUtilization": (
                "100 × SurveyDurationHours / TargetDurationHours  (weekly only)"
            ),
            "SurveysCarDay": "SurveyCount / TotalSurveyors / DaysCount  (weekly only)",
            "DaysCount": "Days in ISO week (capped at today for current week)",
        },
        "notes": (
            "Weekly metrics use KPI_Utilization WorkingDays and WorkingHours. "
            "Yearly aggregation (empty period_dict) skips week-dependent metrics."
        ),
    },
}

INGESTION_PIPELINES = {
    "ReportSummaryIngester": {
        "title": "ReportSummaryIngester → KPI_ReportSummary",
        "sources": ["LSDB (Report, ReportArea, ReportCompliance, …)", "DataHub (EU1/EU2 only)"],
        "steps": [
            "Filter reports with Final Checkbox label, DateStarted >= STARTING_DATE",
            "Query report lengths and coverage from LSDB via get_reports()",
            "For EU1/EU2: merge boundary metadata from DataHub",
            "Derive ReportYear, ReportMonth, ReportWeek from ReportDate",
            "Upsert into KPI_ReportSummary (PK: ReportId)",
        ],
        "target": "KPI_ReportSummary",
    },
    "EmissionSourceSummaryIngester": {
        "title": "EmissionSourceSummaryIngester → KPI_EmissionSourceSummary",
        "sources": ["LSDB EmissionSource table"],
        "steps": [
            "Select reports in update window from KPI_ReportSummary",
            "Query emission sources per report from LSDB",
            "Group by ReportId → summarize_emission():",
            "  • Filter Disposition != 2 for counts; IsFiltered == 0 for LisaPSCount",
            "  • Sum EmissionRate; convert to LPM (× 0.471947)",
            "  • Count bins B0, B1, B-1, B-2 from RepresentativeBinLabel",
            "  • Count dispositions: NG(1), Not_NG(2), PG(3)",
            "Left-merge with all reports; fill missing with 0",
            "Upsert into KPI_EmissionSourceSummary (PK: ReportId)",
        ],
        "target": "KPI_EmissionSourceSummary",
    },
    "SurveySummaryIngester": {
        "title": "SurveySummaryIngester → KPI_SurveySummary",
        "sources": ["LSDB Survey + Segment tables", "KPI_ReportSummary (ReportArea geometry)"],
        "steps": [
            "Query surveys and segments for reports in update window",
            "For each report: geo-intersect segments with ReportArea (UTM projection)",
            "Classify segments: Day/Night (sunrise/sunset), Active/Idle (speed threshold)",
            "Aggregate per SurveyId+ReportId: km, segments, idle/active time, avg speed",
            "Merge with survey metadata; compute SegmentWeight and weighted duration",
            "Upsert into KPI_SurveySummary (PK: SurveyId, ReportId)",
        ],
        "target": "KPI_SurveySummary",
    },
    "PeakSATIngester": {
        "title": "PeakSATIngester → KPI_PeakAboveSAT",
        "sources": ["Box Excel (via KPI_PeakSATLocation)"],
        "steps": [
            "Look up BoxFileId from KPI_PeakSATLocation for customer",
            "Download Excel; compare row count with existing KPI_PeakAboveSAT",
            "If new or mismatched: load all rows, add CustomerId, ReportYear, rename Region",
            "Upsert into KPI_PeakAboveSAT (PK: PeakId)",
        ],
        "target": "KPI_PeakAboveSAT",
    },
}


def iter_tables():
    import lib.tables.IngesterTables as mod

    for name in sorted(dir(mod)):
        obj = getattr(mod, name)
        if isinstance(obj, KPITable):
            yield obj


def column_key(column):
    key = getattr(column, "key", None)
    return "" if key is None else str(key)


# ---------------------------------------------------------------------------
# Diagram helpers (matplotlib)
# ---------------------------------------------------------------------------
BOX_COLORS = {
    "source": "#d6e4f0",
    "process": "#fff2cc",
    "table": "#d5e8d4",
    "kpi": "#e1d5e7",
    "arrow": "#4a4a4a",
}


def _draw_box(ax, x, y, w, h, text, color, fontsize=8):
    box = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.02",
        facecolor=color,
        edgecolor="#333333",
        linewidth=1.2,
    )
    ax.add_patch(box)
    ax.text(
        x + w / 2,
        y + h / 2,
        text,
        ha="center",
        va="center",
        fontsize=fontsize,
        wrap=True,
    )


def _arrow(ax, x1, y1, x2, y2, style="-"):
    ax.annotate(
        "",
        xy=(x2, y2),
        xytext=(x1, y1),
        arrowprops=dict(
            arrowstyle="->",
            color=BOX_COLORS["arrow"],
            lw=1.5,
            linestyle=style,
        ),
    )


def draw_ingestion_diagram(name: str, spec: dict, path: str) -> str:
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5)
    ax.axis("off")
    ax.set_title(spec["title"], fontsize=11, fontweight="bold", pad=10)

    n_sources = len(spec["sources"])
    for i, src in enumerate(spec["sources"]):
        _draw_box(ax, 0.3, 3.5 - i * 0.9, 2.4, 0.7, src, BOX_COLORS["source"], 7)

    _draw_box(ax, 3.5, 2.0, 3.0, 2.5, "\n".join(spec["steps"][:6]), BOX_COLORS["process"], 6.5)
    _draw_box(ax, 7.2, 2.5, 2.3, 1.0, spec["target"], BOX_COLORS["table"], 9)

    for i in range(n_sources):
        _arrow(ax, 2.7, 3.85 - i * 0.9, 3.5, 3.2)
    _arrow(ax, 6.5, 3.0, 7.2, 3.0)

    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def draw_kpi_diagram(name: str, spec: dict, path: str) -> str:
    fig, ax = plt.subplots(figsize=(11, 6))
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 6)
    ax.axis("off")
    ax.set_title(spec["title"], fontsize=11, fontweight="bold", pad=10)

    tables = spec["source_tables"]
    for i, tbl in enumerate(tables):
        _draw_box(ax, 0.2, 4.5 - i * 1.1, 2.6, 0.8, tbl, BOX_COLORS["table"], 7.5)

    group_text = "GROUP BY\n" + ", ".join(spec["group_by"])
    _draw_box(ax, 3.3, 3.5, 2.2, 1.2, group_text, BOX_COLORS["process"], 8)

    if "denominator" in spec:
        _draw_box(
            ax,
            3.3,
            2.0,
            2.2,
            0.8,
            f"Denominator:\n{spec['denominator']}",
            "#fde9d9",
            7,
        )

    outputs = list(spec["outputs"].items())
    n = len(outputs)
    col_h = min(0.55, 3.5 / max(n, 1))
    for i, (kpi, formula) in enumerate(outputs):
        y = 5.0 - i * col_h
        label = f"{kpi}\n{formula}" if len(formula) < 60 else f"{kpi}\n{fill(formula, 50)}"
        _draw_box(ax, 6.0, y - col_h + 0.1, 4.7, col_h - 0.05, label, BOX_COLORS["kpi"], 5.5)

    for i in range(len(tables)):
        _arrow(ax, 2.8, 4.9 - i * 1.1, 3.3, 4.1)
    _arrow(ax, 5.5, 4.1, 6.0, 4.5)

    if spec.get("notes"):
        ax.text(0.2, 0.3, spec["notes"], fontsize=7, style="italic", wrap=True)

    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def draw_overview_diagram(path: str) -> str:
    fig, ax = plt.subplots(figsize=(13, 8))
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 8)
    ax.axis("off")
    ax.set_title("KPIHub Data Flow Overview", fontsize=13, fontweight="bold")

    # Column x-positions
    SRC_X, ING_X, TBL_X, PROC_X, OUT_X = 0.3, 3.2, 5.8, 8.8, 11.3
    SRC_W, ING_W, TBL_W, PROC_W, OUT_W = 2.0, 2.2, 2.5, 2.0, 1.4

    pipelines = [
        {
            "y": 6.0,
            "sources": [("LSDB", 6.15), ("DataHub", 5.35)],
            "ingester": "ReportSummary\nIngester",
            "table": "KPI_Report\nSummary",
        },
        {
            "y": 4.5,
            "sources": [("LSDB", 4.65)],
            "ingester": "EmissionSource\nIngester",
            "table": "KPI_Emission\nSourceSummary",
        },
        {
            "y": 3.0,
            "sources": [("LSDB", 3.15)],
            "ingester": "SurveySummary\nIngester",
            "table": "KPI_Survey\nSummary",
        },
        {
            "y": 1.5,
            "sources": [("Box Excel", 1.65)],
            "ingester": "PeakSAT\nIngester",
            "table": "KPI_PeakAbove\nSAT",
        },
    ]

    table_centers = []
    for pipe in pipelines:
        y = pipe["y"]
        # Sources
        for src_label, src_y in pipe["sources"]:
            _draw_box(ax, SRC_X, src_y - 0.35, SRC_W, 0.7, src_label, BOX_COLORS["source"], 9)
            _arrow(ax, SRC_X + SRC_W, src_y, ING_X, y + 0.4)

        # Ingester
        _draw_box(ax, ING_X, y, ING_W, 0.8, pipe["ingester"], BOX_COLORS["process"], 7.5)
        _arrow(ax, ING_X + ING_W, y + 0.4, TBL_X, y + 0.4)

        # Target table
        _draw_box(ax, TBL_X, y, TBL_W, 0.8, pipe["table"], BOX_COLORS["table"], 7.5)
        table_centers.append((TBL_X + TBL_W, y + 0.4))

    # SurveySummary also reads ReportArea from KPI_ReportSummary
    _arrow(ax, TBL_X + TBL_W / 2, 6.0, ING_X + ING_W / 2, 3.8, style="--")

    # KPI processors and output
    proc_y = 3.5
    _draw_box(ax, PROC_X, proc_y, PROC_W, 1.6, "KPIReport.py\nProcessors", BOX_COLORS["process"], 8)
    _draw_box(ax, OUT_X, proc_y + 0.3, OUT_W, 1.0, "KPI_Data", BOX_COLORS["kpi"], 9)

    for tbl_x, tbl_y in table_centers:
        _arrow(ax, tbl_x, tbl_y, PROC_X, proc_y + 0.8)

    _arrow(ax, PROC_X + PROC_W, proc_y + 0.8, OUT_X, proc_y + 0.8)

    # Legend for dashed line
    ax.text(
        TBL_X,
        0.4,
        "Dashed: SurveySummary reads ReportArea from KPI_ReportSummary",
        fontsize=7,
        style="italic",
        color="#555555",
    )

    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def generate_diagrams() -> dict[str, str]:
    os.makedirs(DIAGRAMS_DIR, exist_ok=True)
    paths = {}

    paths["overview"] = draw_overview_diagram(os.path.join(DIAGRAMS_DIR, "00_overview.png"))

    for name, spec in INGESTION_PIPELINES.items():
        p = os.path.join(DIAGRAMS_DIR, f"ingest_{name}.png")
        paths[f"ingest_{name}"] = draw_ingestion_diagram(name, spec, p)

    for name, spec in KPI_PROCESSORS.items():
        p = os.path.join(DIAGRAMS_DIR, f"kpi_{name}.png")
        paths[f"kpi_{name}"] = draw_kpi_diagram(name, spec, p)

    return paths


# ---------------------------------------------------------------------------
# PDF builder
# ---------------------------------------------------------------------------
def build_pdf(diagram_paths: dict[str, str], output_path: str = OUTPUT_PDF) -> str:
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "DocTitle", parent=styles["Heading1"], fontSize=20, spaceAfter=14
    )
    h1 = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=15, spaceBefore=12, spaceAfter=8)
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=12, spaceBefore=8, spaceAfter=6)
    body = styles["Normal"]
    small = ParagraphStyle("Small", parent=body, fontSize=8, leading=10)
    cell = ParagraphStyle("Cell", parent=body, fontSize=7, leading=9)
    cell_col = ParagraphStyle("CellCol", parent=body, fontSize=7, leading=9)
    formula_style = ParagraphStyle("Formula", parent=body, fontSize=8, leftIndent=12)

    # Usable page width on A4 with 1.5 cm margins ≈ 18 cm
    PAGE_W = 18.0 * cm

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

    # ---- Cover ----
    story.append(Paragraph("KPIHub SQLite Documentation", title_style))
    #story.append(
    #    Paragraph(
    #        f"Auto-generated from <b>lib/</b> on {datetime.now():%Y-%m-%d %H:%M}",
    #        body,
    #    )
    #)
    story.append(Spacer(1, 0.3 * cm))
    story.append(
        Paragraph(
            "This document describes all database tables, ingestion pipelines, "
            "and KPI calculation logic implemented in the KPIHub SQLite module.",
            body,
        )
    )
    story.append(PageBreak())

    # ---- Overview diagram ----
    story.append(Paragraph("1. System Overview", h1))
    story.append(
        Paragraph(
            "High-level data flow from external sources through ingesters, "
            "summary tables, KPI processors, and into KPI_Data.",
            body,
        )
    )
    story.append(Spacer(1, 0.2 * cm))
    overview_img = Image(diagram_paths["overview"], width=17 * cm, height=11 * cm)
    story.append(overview_img)
    story.append(PageBreak())

    # ---- Table reference ----
    story.append(Paragraph("2. Table Reference", h1))
    story.append(Paragraph(f"Total tables: <b>{len(tables)}</b>", body))
    story.append(Spacer(1, 0.3 * cm))

    index_data = [["#", "Table", "Cols", "Description"]]
    for i, table in enumerate(tables, start=1):
        desc = TABLE_DESCRIPTIONS.get(table.name, "")
        index_data.append([
            str(i),
            Paragraph(table.name, cell),
            str(len(table.columns)),
            Paragraph(desc, cell),
        ])

    idx_col_widths = [0.7 * cm, 3.8 * cm, 1.0 * cm, PAGE_W - 5.5 * cm]
    idx_table = Table(index_data, colWidths=idx_col_widths, repeatRows=1)
    idx_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e79")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 7),
                ("FONTSIZE", (0, 1), (-1, -1), 7),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eef3f8")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(idx_table)
    story.append(PageBreak())

    # Per-table detail: # | Column | Type | Key | Description
    col_widths = [0.5 * cm, 2.5 * cm, 2.5 * cm, 1.0 * cm, PAGE_W - 6.5 * cm]

    for table in tables:
        desc = TABLE_DESCRIPTIONS.get(table.name, "No description available.")
        col_data = [["#", "Column", "Type", "Key", "Description"]]
        for i, column in enumerate(table.columns, start=1):
            col_desc = get_column_description(table.name, column.name)
            dtype = str(getattr(column, "datatype", "") or "")
            col_data.append([
                str(i),
                Paragraph(column.name, cell_col),
                dtype,
                column_key(column) or "—",
                Paragraph(col_desc, cell),
            ])

        col_table = Table(col_data, colWidths=col_widths, repeatRows=1)
        col_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2e75b6")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 7),
                    ("FONTSIZE", (0, 1), (-1, -1), 7),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("VALIGN", (2, 1), (3, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        story.append(Paragraph(table.name, h2))
        story.append(Paragraph(desc, body))
        story.append(Paragraph(f"Columns: <b>{len(table.columns)}</b>", small))
        story.append(Spacer(1, 0.15 * cm))
        story.append(col_table)
        story.append(Spacer(1, 0.6 * cm))

    story.append(PageBreak())

    # ---- Ingestion pipelines ----
    story.append(Paragraph("3. Ingestion Pipelines", h1))
    story.append(
        Paragraph(
            "Each ingester extends <b>IngesterClass.Ingester</b>: update_check → query_data → "
            "push_data → sanity_check. Data is upserted into the target KPI table.",
            body,
        )
    )
    story.append(Spacer(1, 0.3 * cm))

    for name, spec in INGESTION_PIPELINES.items():
        story.append(Paragraph(spec["title"], h2))
        story.append(Paragraph(f"<b>Sources:</b> {', '.join(spec['sources'])}", body))
        story.append(Paragraph("<b>Steps:</b>", body))
        for step in spec["steps"]:
            story.append(Paragraph(f"• {step}", formula_style))
        story.append(Paragraph(f"<b>Target table:</b> {spec['target']}", body))
        img_key = f"ingest_{name}"
        if img_key in diagram_paths:
            story.append(Spacer(1, 0.2 * cm))
            story.append(Image(diagram_paths[img_key], width=16 * cm, height=8 * cm))
        story.append(Spacer(1, 0.4 * cm))

    story.append(PageBreak())

    # ---- KPI calculations ----
    story.append(Paragraph("4. KPI Calculations (KPIReport.py)", h1))
    story.append(
        Paragraph(
            "All KPI classes extend <b>KPISummary</b>: query_table → process_data "
            "(groupby + processor) → melter → push_data to KPI_Data.",
            body,
        )
    )
    story.append(Spacer(1, 0.3 * cm))

    for name, spec in KPI_PROCESSORS.items():
        story.append(Paragraph(spec["title"], h2))
        story.append(
            Paragraph(
                f"<b>Source tables:</b> {', '.join(spec['source_tables'])} &nbsp;|&nbsp; "
                f"<b>Group by:</b> {', '.join(spec['group_by'])}",
                body,
            )
        )
        if "denominator" in spec:
            story.append(Paragraph(f"<b>Denominator:</b> {spec['denominator']}", body))
        if spec.get("notes"):
            story.append(Paragraph(spec["notes"], small))

        kpi_data = [["KPI", "Formula / Definition"]]
        for kpi, formula in spec["outputs"].items():
            kpi_data.append([kpi, formula])

        kpi_table = Table(kpi_data, colWidths=[4.5 * cm, 12.5 * cm])
        kpi_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#7030a0")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 7),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3edf7")]),
                ]
            )
        )
        story.append(kpi_table)

        img_key = f"kpi_{name}"
        if img_key in diagram_paths:
            story.append(Spacer(1, 0.2 * cm))
            story.append(Image(diagram_paths[img_key], width=17 * cm, height=9 * cm))
        story.append(Spacer(1, 0.5 * cm))

    doc.build(story)
    return output_path


def main():
    print("Generating diagrams...")
    diagram_paths = generate_diagrams()
    print(f"  {len(diagram_paths)} diagrams written to {DIAGRAMS_DIR}")

    print("Building PDF...")
    pdf_path = build_pdf(diagram_paths)
    print(f"Wrote {pdf_path}")


if __name__ == "__main__":
    main()
