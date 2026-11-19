-- Weekly_KPI view mirroring SQLite/tools/KPIOutput/ViewCreator/KPIHub_EKPI_View.ipynb
--
-- Pivots kpihub."KPI_Data" weekly rows into one column per KPI for Excel/output tooling.
--
-- Prerequisite:
--   IngesterTables.sql, InitKPI.sql, KPI processor scripts (KPIReport.sql, etc.)
--
-- Setup:
--   psql -U dsoler -d Datanalytics -v ON_ERROR_STOP=1 -f Weekly_KPI.sql
--

DROP VIEW IF EXISTS kpihub."Weekly_KPI";

CREATE VIEW kpihub."Weekly_KPI" AS
SELECT
  kd."Year",
  kd.periodvalue AS "PeriodValue",
  kc."Name" AS "CustomerName",
  kd.boundaryregion AS "BoundaryRegion",
  SUM(CASE WHEN kd.kpiid = 'ReportAssetLengthKm' THEN kd."Value"::double precision END) AS "ReportAssetLengthKm",
  SUM(CASE WHEN kd.kpiid = 'AssetCoveredLengthKm' THEN kd."Value"::double precision END) AS "AssetCoveredLengthKm",
  SUM(CASE WHEN kd.kpiid = 'DistributionPipeKm' THEN kd."Value"::double precision END) AS "DistributionPipeKm",
  SUM(CASE WHEN kd.kpiid = 'DistributionPipeCoveredKm' THEN kd."Value"::double precision END) AS "DistributionPipeCoveredKm",
  SUM(CASE WHEN kd.kpiid = 'CumulativeAssetCoveredLengthKm' THEN kd."Value"::double precision END) AS "CumulativeAssetCoveredLengthKm",
  SUM(CASE WHEN kd.kpiid = 'ServicePipeKm' THEN kd."Value"::double precision END) AS "ServicePipeKm",
  SUM(CASE WHEN kd.kpiid = 'ServicePipeCoveredKm' THEN kd."Value"::double precision END) AS "ServicePipeCoveredKm",
  SUM(CASE WHEN kd.kpiid = 'ReportCount' THEN kd."Value"::double precision END) AS "ReportCount",
  SUM(CASE WHEN kd.kpiid = 'DaysCount' THEN kd."Value"::double precision END) AS "DaysCount",
  SUM(CASE WHEN kd.kpiid = 'FOVMain' THEN kd."Value"::double precision END) AS "FOVMain",
  SUM(CASE WHEN kd.kpiid = 'SurveyDurationHours' THEN kd."Value"::double precision END) AS "SurveyDurationHours",
  SUM(CASE WHEN kd.kpiid = 'TargetDurationHours' THEN kd."Value"::double precision END) AS "TargetDurationHours",
  SUM(CASE WHEN kd.kpiid = 'CustomerUtilization' THEN kd."Value"::double precision END) AS "CustomerUtilization",
  SUM(CASE WHEN kd.kpiid = 'StarndardUtilization' THEN kd."Value"::double precision END) AS "StarndardUtilization",
  SUM(CASE WHEN kd.kpiid = 'TotalSurveyors' THEN kd."Value"::double precision END) AS "TotalSurveyors",
  SUM(CASE WHEN kd.kpiid = 'ProductivityPerSurveyor' THEN kd."Value"::double precision END) AS "ProductivityPerSurveyor",
  SUM(CASE WHEN kd.kpiid = 'SurveyCount' THEN kd."Value"::double precision END) AS "SurveyCount",
  SUM(CASE WHEN kd.kpiid = 'AvgSpeedKm' THEN kd."Value"::double precision END) AS "AvgSpeedKm",
  SUM(CASE WHEN kd.kpiid = 'SurveysCarDay' THEN kd."Value"::double precision END) AS "SurveysCarDay",
  SUM(CASE WHEN kd.kpiid = 'IdleTime' THEN kd."Value"::double precision END) AS "IdleTime",
  SUM(CASE WHEN kd.kpiid = 'TotalDrivenLengthKm' THEN kd."Value"::double precision END) AS "TotalDrivenLengthKm",
  SUM(CASE WHEN kd.kpiid = 'DrivingRatio' THEN kd."Value"::double precision END) AS "DrivingRatio",
  SUM(CASE WHEN kd.kpiid = 'NightDrivenLength' THEN kd."Value"::double precision END) AS "NightDrivenLength",
  SUM(CASE WHEN kd.kpiid = 'DayDrivenLength' THEN kd."Value"::double precision END) AS "DayDrivenLength",
  SUM(CASE WHEN kd.kpiid = 'NightRatio' THEN kd."Value"::double precision END) AS "NightRatio",
  SUM(CASE WHEN kd.kpiid = 'DayRatio' THEN kd."Value"::double precision END) AS "DayRatio",
  SUM(CASE WHEN kd.kpiid = 'PeakAboveSATCount' THEN kd."Value"::double precision END) AS "PeakAboveSATCount",
  SUM(CASE WHEN kd.kpiid = 'LisaCount' THEN kd."Value"::double precision END) AS "LisaCount",
  SUM(CASE WHEN kd.kpiid = 'EmissionRate' THEN kd."Value"::double precision END) AS "EmissionRate",
  SUM(CASE WHEN kd.kpiid = 'B0Count' THEN kd."Value"::double precision END) AS "B0Count",
  SUM(CASE WHEN kd.kpiid = 'B1Count' THEN kd."Value"::double precision END) AS "B1Count",
  SUM(CASE WHEN kd.kpiid = 'Bm1Count' THEN kd."Value"::double precision END) AS "Bm1Count",
  SUM(CASE WHEN kd.kpiid = 'Bm2Count' THEN kd."Value"::double precision END) AS "Bm2Count",
  SUM(CASE WHEN kd.kpiid = 'NGCount' THEN kd."Value"::double precision END) AS "NGCount",
  SUM(CASE WHEN kd.kpiid = 'PGCount' THEN kd."Value"::double precision END) AS "PGCount",
  SUM(CASE WHEN kd.kpiid = 'Not_NGCount' THEN kd."Value"::double precision END) AS "Not_NGCount",
  SUM(CASE WHEN kd.kpiid = 'LisaDensity' THEN kd."Value"::double precision END) AS "LisaDensity",
  SUM(CASE WHEN kd.kpiid = 'InstatanoeusEmission' THEN kd."Value"::double precision END) AS "InstatanoeusEmission",
  SUM(CASE WHEN kd.kpiid = 'B0Density' THEN kd."Value"::double precision END) AS "B0Density",
  SUM(CASE WHEN kd.kpiid = 'B1Density' THEN kd."Value"::double precision END) AS "B1Density",
  SUM(CASE WHEN kd.kpiid = 'Bm1Density' THEN kd."Value"::double precision END) AS "Bm1Density",
  SUM(CASE WHEN kd.kpiid = 'Bm2Density' THEN kd."Value"::double precision END) AS "Bm2Density",
  SUM(CASE WHEN kd.kpiid = 'B0Share' THEN kd."Value"::double precision END) AS "B0Share",
  SUM(CASE WHEN kd.kpiid = 'B1Share' THEN kd."Value"::double precision END) AS "B1Share",
  SUM(CASE WHEN kd.kpiid = 'Bm1Share' THEN kd."Value"::double precision END) AS "Bm1Share",
  SUM(CASE WHEN kd.kpiid = 'Bm2Share' THEN kd."Value"::double precision END) AS "Bm2Share",
  SUM(CASE WHEN kd.kpiid = 'NGShare' THEN kd."Value"::double precision END) AS "NGShare",
  SUM(CASE WHEN kd.kpiid = 'PGShare' THEN kd."Value"::double precision END) AS "PGShare",
  SUM(CASE WHEN kd.kpiid = 'Not_NGShare' THEN kd."Value"::double precision END) AS "Not_NGShare",
  SUM(CASE WHEN kd.kpiid = 'POR' THEN kd."Value"::double precision END) AS "POR",
  SUM(CASE WHEN kd.kpiid = 'CurrentCompletion' THEN kd."Value"::double precision END) AS "CurrentCompletion"
FROM kpihub."KPI_Data" kd
LEFT JOIN kpihub."KPI_Customer" kc ON kd.customerid = kc.customerid
WHERE kd.periodtype = 'Week'
GROUP BY
  kd."Year",
  kd.periodvalue,
  kd.customerid,
  kc."Name",
  kd.boundaryregion;

COMMENT ON VIEW kpihub."Weekly_KPI" IS
  'Weekly KPI pivot for output/Excel. Mirrors SQLite Weekly_KPI view.';
