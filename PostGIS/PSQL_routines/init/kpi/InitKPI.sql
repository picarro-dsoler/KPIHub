-- KPI definition seed mirroring SQLite/init/InitKPI.py
--
-- Upserts all KPI metadata rows into kpihub."KPI_Definition".
--
-- Prerequisite:
--   IngesterTables.sql (creates kpihub."KPI_Definition")
--
-- Setup:
--   psql -U dsoler -d Datanalytics -v ON_ERROR_STOP=1 -f InitKPI.sql
--
INSERT INTO kpihub."KPI_Definition" (
  "Name", unit, formula, description, lastupdated
)
SELECT
  v.name,
  v.unit,
  v.formula,
  v.description,
  NOW()
FROM (VALUES
  ('PeriodValue', '', '', 'Number of the week starting from 1st of Jan'),
  ('ReportAssetLengthKm', 'Km', '', 'Total length of all the assets in the specified period'),
  ('AssetCoveredLengthKm', 'Km', '', 'Total length of all the assets covered in the report'),
  ('CumulativeAssetCoveredLengthKm', 'Km', '', 'Cumulative covered length of all the assets covered in the indicated period'),
  ('DistributionPipeKm', 'Km', '', 'Total length of all the mains in the report'),
  ('DistributionPipeCoveredKm', 'Km', '', 'Total length of all the mains covered in the report'),
  ('ServicePipeKm', 'Km', '', 'Total length of all the services in the report'),
  ('ServicePipeCoveredKm', 'Km', '', 'Total length of all the services covered in the report'),
  ('ReportCount', 'Report', '', 'Total number of reports in the specified week'),
  ('DaysCount', 'Day', '', 'Total number of days worked in the specified week'),
  ('FOVMain', 'Percent', 'DistributionPipeCoveredKm / DistributionPipeKm', 'Km of mains covered over the total Km of mains'),
  ('SurveyDurationHours', 'Hours', '', 'Total hours driven by all cars in the week'),
  ('TargetDurationHours', 'Hours', '', 'Exepected total number hours driven by all cars available. i.e 7 days * 7 hours * 25 cars'),
  ('CustomerUtilization', 'Percent', 'SurveyDurationHours / TargetDurationHours', 'Total hours driven by all cars in the week over the expected total number hours driven by all cars available. i.e 7 days * 7 hours * 25 cars'),
  ('StarndardUtilization', 'Percent', 'SurveyDurationHours / TargetDurationHours', 'Total hours driven by all cars in the week over the expected total number hours driven by all cars available. i.e 6 days * 5 hours * 25 cars'),
  ('TotalSurveyors', 'Surveyor', '', 'Total number of surveyors in the specified week'),
  ('ProductivityPerSurveyor', 'Km / Surveyor', 'DistributionPipeCoveredKm / TotalSurveyors', 'Total length of all the assets covered in the report over the total number of surveyors in the specified week'),
  ('SurveyCount', 'Survey', '', 'Total number of surveys in the  specified week'),
  ('AvgSpeedKm', 'Km/h', '', 'Average speed counting all the cars in the specified week'),
  ('SurveysCarDay', 'Survey / Car / Day', 'SurveyCount / TotalSurveyors / DaysCount', 'Total number of surveys per car per day in the specified week'),
  ('IdleTime', 'Percent', 'IdleTimeMinutes / SurveyDurationMinutes', 'Ratio of idle time over the total survey duration'),
  ('TotalDrivenLengthKm', 'Km', '', 'Total length driven in the specified week'),
  ('DrivingRatio', 'Ratio', 'TotalKilometers / DistributionPipeCoveredKm', 'Total length driven in the specified week over Total length of all the assets covered in the report'),
  ('NightDrivenLength', 'Km', '', 'Total length covered during the night in the specified week'),
  ('DayDrivenLength', 'Km', '', 'Total length covered during the day in the specified week'),
  ('NightRatio', 'Percent', '', 'NightKm / TotalKilometers'),
  ('DayRatio', 'Percent', '', 'DayKm / TotalKilometers'),
  ('PeakAboveSATCount', 'Peak', '', 'Total number of peaks above SAT in the specified week'),
  ('LisaCount', 'Lisa', '', 'Total number of Lisa in the specified week, (No Disposition 2)'),
  ('LisaPSCount', 'Lisa', '', 'Total number of Lisa in the specified week, (No Disposition 2 and IsFiltered 1)'),
  ('EmissionRate', 'SCFH', '', 'Total emission rate in the specified week, (No Disposition 2)'),
  ('EmissionRateLPM', 'LPM', 'EmissionRate * 0.471947', 'Total emission rate in the specified week, (No Disposition 2)'),
  ('RepresentativeEmissionRate', 'SCFH', '', 'Total representative emission rate in the specified week, (No Disposition 2)'),
  ('RepresentativeEmissionRateLPM', 'LPM', 'RepresentativeEmissionRate * 0.471947', 'Total representative emission rate in the specified week, (No Disposition 2)'),
  ('B0RepEmissionRate', 'SCFH', '', 'Total B0 representative emission rate in the specified week, (No Disposition 2)'),
  ('B1RepEmissionRate', 'SCFH', '', 'Total B1 representative emission rate in the specified week, (No Disposition 2)'),
  ('Bm1RepEmissionRate', 'SCFH', '', 'Total B-1 representative emission rate in the specified week, (No Disposition 2)'),
  ('Bm2RepEmissionRate', 'SCFH', '', 'Total B-2 representative emission rate in the specified week, (No Disposition 2)'),
  ('B0RepEmissionRateLPM', 'LPM', 'B0RepEmissionRate * 0.471947', 'Total B0 representative emission rate in the specified week, (No Disposition 2)'),
  ('B1RepEmissionRateLPM', 'LPM', 'B1RepEmissionRate * 0.471947', 'Total B1 representative emission rate in the specified week, (No Disposition 2)'),
  ('Bm1RepEmissionRateLPM', 'LPM', 'Bm1RepEmissionRate * 0.471947', 'Total B-1 representative emission rate in the specified week, (No Disposition 2)'),
  ('Bm2RepEmissionRateLPM', 'LPM', 'Bm2RepEmissionRate * 0.471947', 'Total B-2 representative emission rate in the specified week, (No Disposition 2)'),
  ('B0Count', 'Lisa', '', 'Total number of B0 in the specified week, (No Disposition 2)'),
  ('B1Count', 'Lisa', '', 'Total number of B1 in the specified week, (No Disposition 2)'),
  ('Bm1Count', 'Lisa', '', 'Total number of B-1 in the specified week, (No Disposition 2)'),
  ('Bm2Count', 'Lisa', '', 'Total number of B-2 in the specified week, (No Disposition 2)'),
  ('NGCount', 'Lisa', '', 'Total number of NG in the specified week, (With Disposition 2)'),
  ('PGCount', 'Lisa', '', 'Total number of PG in the specified week, (With Disposition 2)'),
  ('Not_NGCount', 'Lisa', '', 'Total number of Not NG in the specified week, (With Disposition 2)'),
  ('LisaDensity', 'Lisa / Km', 'LisaCount / DistributionPipeCoveredKm', 'Number of Lisa per Km of Asset Covered'),
  ('InstantanoeusEmission', 'SCFH / Km', 'EmissionRate / DistributionPipeCoveredKm', 'Emission rate per Km of Asset Covered'),
  ('InstantanoeusEmissionLPM', 'LPM / Km', 'InstatanoeusEmission * 0.471947 / DistributionPipeCoveredKm', 'Emission rate per Km of Asset Covered'),
  ('InstantaneousRepEmission', 'SCFH / Km', 'RepresentativeEmissionRate / DistributionPipeCoveredKm', 'Representative emission rate per Km of Asset Covered'),
  ('InstantaneousRepEmissionLPM', 'LPM / Km', 'InstantaneousRepEmission * 0.471947 / DistributionPipeCoveredKm', 'Representative emission rate per Km of Asset Covered'),
  ('InstantaneousRepEmissionB1', 'SCFH / Km', 'B1RepEmissionRate / DistributionPipeCoveredKm', 'B1 representative emission rate per Km of Asset Covered'),
  ('InstantaneousRepEmissionB1LPM', 'LPM / Km', 'InstantaneousRepEmissionB1 * 0.471947 / DistributionPipeCoveredKm', 'B1 representative emission rate per Km of Asset Covered'),
  ('InstantaneousRepEmissionB0', 'SCFH / Km', 'B0RepEmissionRate / DistributionPipeCoveredKm', 'B0 representative emission rate per Km of Asset Covered'),
  ('InstantaneousRepEmissionB0LPM', 'LPM / Km', 'InstantaneousRepEmissionB0 * 0.471947 / DistributionPipeCoveredKm', 'B0 representative emission rate per Km of Asset Covered'),
  ('InstantaneousRepEmissionBm1', 'SCFH / Km', 'Bm1RepEmissionRate / DistributionPipeCoveredKm', 'B-1 representative emission rate per Km of Asset Covered'),
  ('InstantaneousRepEmissionBm1LPM', 'LPM / Km', 'InstantaneousRepEmissionBm1 * 0.471947 / DistributionPipeCoveredKm', 'B-1 representative emission rate per Km of Asset Covered'),
  ('InstantaneousRepEmissionBm2', 'SCFH / Km', 'Bm2RepEmissionRate / DistributionPipeCoveredKm', 'B-2 representative emission rate per Km of Asset Covered'),
  ('InstantaneousRepEmissionBm2LPM', 'LPM / Km', 'InstantaneousRepEmissionBm2 * 0.471947 / DistributionPipeCoveredKm', 'B-2 representative emission rate per Km of Asset Covered'),
  ('B0Density', 'Lisa / Km', 'B0Count / DistributionPipeCoveredKm', 'Number of B0 per Km of Asset Covered'),
  ('B1Density', 'Lisa / Km', 'B1Count / DistributionPipeCoveredKm', 'Number of B1 per Km of Asset Covered'),
  ('Bm1Density', 'Lisa / Km', 'Bm1Count / DistributionPipeCoveredKm', 'Number of B-1 per Km of Asset Covered'),
  ('Bm2Density', 'Lisa / Km', 'Bm2Count / DistributionPipeCoveredKm', 'Number of B-2 per Km of Asset Covered'),
  ('B0Share', 'Percent', 'B0Count / LisaCount', 'Number of B0 per Lisa'),
  ('B1Share', 'Percent', 'B1Count / LisaCount', 'Number of B1 per Lisa'),
  ('Bm1Share', 'Percent', 'Bm1Count / LisaCount', 'Number of B-1 per Lisa'),
  ('Bm2Share', 'Percent', 'Bm2Count / LisaCount', 'Number of B-2 per Lisa'),
  ('NGShare', 'Percent', 'NGCount / (NGCount + Not_NGCount + PGCount)', 'Number of NG per Lisa'),
  ('PGShare', 'Percent', 'PGCount / (NGCount + Not_NGCount + PGCount)', 'Number of PG per Lisa'),
  ('Not_NGShare', 'Percent', 'Not_NGCount / (NGCount + Not_NGCount + PGCount)', 'Number of Not NG per Lisa'),
  ('POR', 'Km', '', 'Total Km of the POR in the year'),
  ('CurrentCompletion', 'Percent', 'CumulativeAssetCoveredLengthKm / POR', 'Current completion of the network based on the POR')
) AS v(name, unit, formula, description)
ON CONFLICT ("Name") DO UPDATE SET
  unit = EXCLUDED.unit,
  formula = EXCLUDED.formula,
  description = EXCLUDED.description,
  lastupdated = EXCLUDED.lastupdated;

SELECT COUNT(*) AS kpi_definition_count FROM kpihub."KPI_Definition";
