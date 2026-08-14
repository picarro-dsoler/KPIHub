-- Auto-generated from lib/tables/IngesterTables.py
-- Idempotent KPIHub table DDL for PostgreSQL/PostGIS
-- Usage: psql -U dsoler -d Datanalytics -v ON_ERROR_STOP=1 -f IngesterTables.sql

CREATE SCHEMA IF NOT EXISTS "kpihub";

-- KPI_Customer
CREATE TABLE IF NOT EXISTS "kpihub"."KPI_Customer" (CustomerId UUID, "Name" TEXT, ShortName TEXT, Active BOOLEAN, DBLocation TEXT, LastUpdated TIMESTAMP, PRIMARY KEY (CustomerId));

-- KPI_POR
CREATE TABLE IF NOT EXISTS "kpihub"."KPI_POR" (CustomerId TEXT, "Year" INTEGER, StartingDate TIMESTAMP, EndingDate TIMESTAMP, Description TEXT, "Value" DOUBLE PRECISION, Unit TEXT, LastUpdated TIMESTAMP, PRIMARY KEY (CustomerId, "Year"));

-- KPI_OutputExcelLocation
CREATE TABLE IF NOT EXISTS "kpihub"."KPI_OutputExcelLocation" (CustomerId UUID, BoxFolderId TEXT, LastUpdated TIMESTAMP, PRIMARY KEY (CustomerId));

-- KPI_ReportDrivingSurvey
CREATE TABLE IF NOT EXISTS "kpihub"."KPI_ReportDrivingSurvey" (Id UUID, ReportId UUID, SurveyId UUID, LastUpdated TIMESTAMP, PRIMARY KEY (Id));

-- KPI_Utilization
CREATE TABLE IF NOT EXISTS "kpihub"."KPI_Utilization" (CustomerId UUID, WorkingDays INTEGER, WorkingHours INTEGER, SunriseHour INTEGER, SunsetHour INTEGER, BaseSurveyorCount INTEGER, Description TEXT, LastUpdated TIMESTAMP, PRIMARY KEY (CustomerId));

-- KPI_ReportSummary
CREATE TABLE IF NOT EXISTS "kpihub"."KPI_ReportSummary" (ReportId UUID, CustomerId UUID, ReportName TEXT, ReportDate TIMESTAMP, ReportYear INTEGER, ReportMonth INTEGER, ReportWeek INTEGER, ReportAssetLengthKm DOUBLE PRECISION, AssetCoveredLengthKm DOUBLE PRECISION, DistributionPipeKm DOUBLE PRECISION, DistributionPipeCoveredKm DOUBLE PRECISION, ServicePipeKm DOUBLE PRECISION, ServicePipeCoveredKm DOUBLE PRECISION, BoundaryName TEXT, BoundaryType TEXT, BoundaryMode TEXT, BoundaryPlant TEXT, BoundarySubplant TEXT, BoundaryRegion TEXT, BoundarySubRegion TEXT, ReportArea TEXT, LastUpdated TIMESTAMP, PRIMARY KEY (ReportId));

-- KPI_PeakSATLocation
CREATE TABLE IF NOT EXISTS "kpihub"."KPI_PeakSATLocation" (CustomerId UUID, BoxFileId INTEGER, LastUpdated TIMESTAMP, PRIMARY KEY (CustomerId));

-- KPI_PeakAboveSAT
CREATE TABLE IF NOT EXISTS "kpihub"."KPI_PeakAboveSAT" (CustomerId UUID, PeakName TEXT, PeakId UUID, "Date" date, ReportYear INTEGER, WeekNumber INTEGER, Disposition TEXT, "LocalTime" TIMESTAMP, BoundaryName TEXT, BoundaryRegion TEXT, EmissionRate DOUBLE PRECISION, PeakGpsLatitude DOUBLE PRECISION, PeakGpsLongitude DOUBLE PRECISION, Easting DOUBLE PRECISION, Northing DOUBLE PRECISION, UserName TEXT, SurveyorUnit TEXT, AnalyzerSerialNumber TEXT, Hyperlink TEXT, LastUpdated TIMESTAMP, PRIMARY KEY (PeakId));

-- KPI_EmissionSourceSummary
CREATE TABLE IF NOT EXISTS "kpihub"."KPI_EmissionSourceSummary" (ReportId UUID, EmissionRate DOUBLE PRECISION, EmissionRateLPM UUID, RepresentativeEmissionRate DOUBLE PRECISION, RepresentativeEmissionRateLPM DOUBLE PRECISION, LisaCount INTEGER, B0Count INTEGER, B1Count INTEGER, Bm1Count INTEGER, Bm2Count INTEGER, B0RepEmissionRateLPM DOUBLE PRECISION, B1RepEmissionRateLPM DOUBLE PRECISION, Bm1RepEmissionRateLPM DOUBLE PRECISION, Bm2RepEmissionRateLPM DOUBLE PRECISION, B0RepEmissionRate DOUBLE PRECISION, B1RepEmissionRate DOUBLE PRECISION, Bm1RepEmissionRate DOUBLE PRECISION, Bm2RepEmissionRate DOUBLE PRECISION, Not_NGCount INTEGER, PGCount INTEGER, NGCount INTEGER, LastUpdated TIMESTAMP, PRIMARY KEY (ReportId));

-- KPI_SurveySummary
CREATE TABLE IF NOT EXISTS "kpihub"."KPI_SurveySummary" (SurveyId UUID, ReportId UUID, SurveyorUnit TEXT, SurveyDurationMinutes DOUBLE PRECISION, SurveyRawDurationMinutes DOUBLE PRECISION, SegmentWeight DOUBLE PRECISION, StartHour INTEGER, StartTime TIMESTAMP, StartEpoch BIGINT, EndTime TIMESTAMP, EndEpoch BIGINT, StartDay date, EndDay date, LateralRotation TEXT, NumberOfPeaks INTEGER, DaySegments INTEGER, NightSegments INTEGER, ActiveSegments INTEGER, IdleSegments INTEGER, TotalSegments INTEGER, TotalSegmentsInSurvey INTEGER, TotalKilometers DOUBLE PRECISION, DayKilometers DOUBLE PRECISION, NightKilometers DOUBLE PRECISION, IdleTimeMinutes DOUBLE PRECISION, ActiveTimeMinutes DOUBLE PRECISION, SegmentDurationMinutes DOUBLE PRECISION, AvgSpeedKm DOUBLE PRECISION, LastUpdated TIMESTAMP, PRIMARY KEY (SurveyId, ReportId));

-- KPI_Definition
CREATE TABLE IF NOT EXISTS "kpihub"."KPI_Definition" ("Name" TEXT, Unit TEXT, Formula TEXT, Description TEXT, LastUpdated TIMESTAMP, PRIMARY KEY ("Name"));

-- KPI_Data
CREATE TABLE IF NOT EXISTS "kpihub"."KPI_Data" (Id TEXT, KPIId TEXT, CustomerId UUID, BoundaryRegion TEXT, "Year" INTEGER, PeriodType INTEGER, PeriodValue INTEGER, "Value" TEXT, DataType TEXT, LastUpdated TIMESTAMP, PRIMARY KEY (Id));

-- Show kpihub tables with plain \dt after reconnecting
DO $$
BEGIN
  EXECUTE format(
    'ALTER DATABASE %I SET search_path TO kpihub, public',
    current_database()
  );
END $$;
