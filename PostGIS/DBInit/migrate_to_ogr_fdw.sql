-- Migrate an existing KPIHub PostGIS database from tds_fdw to ogr_fdw.
-- Rebuild the Docker image first, then run:
--   psql -h localhost -U dsoler -d Datanalytics -v ON_ERROR_STOP=1 -f migrate_to_ogr_fdw.sql
--
-- Verify after migration:
--   SELECT foreign_table_schema, foreign_table_name
--     FROM information_schema.foreign_tables
--     WHERE foreign_table_schema IN ('eu1', 'eu2')
--     ORDER BY 1, 2;
--   SELECT COUNT(*) FROM eu1."Report";

CREATE EXTENSION IF NOT EXISTS ogr_fdw;

DO $$
DECLARE
  r record;
BEGIN
  FOR r IN
    SELECT foreign_table_schema, foreign_table_name
    FROM information_schema.foreign_tables
    WHERE foreign_table_schema IN ('eu1', 'eu2')
  LOOP
    EXECUTE format(
      'DROP FOREIGN TABLE IF EXISTS %I.%I CASCADE',
      r.foreign_table_schema,
      r.foreign_table_name
    );
  END LOOP;
END $$;

DROP SERVER IF EXISTS eu1_srv CASCADE;
DROP SERVER IF EXISTS eu2_srv CASCADE;

CREATE SERVER eu1_srv
  FOREIGN DATA WRAPPER ogr_fdw
  OPTIONS (
    datasource 'MSSQL:server=eu-prd-sqlsrv-ee-db01.czz1yneu9gmr.eu-central-1.rds.amazonaws.com,1433;database=EU-SurveyorProduction;uid=dsoler;pwd=2twN2cY0uIwm;driver=FreeTDS',
    format 'MSSQLSpatial',
    config_options 'MSSQLSPATIAL_LIST_ALL_TABLES=YES MSSQLSPATIAL_USE_GEOMETRY_COLUMNS=NO'
  );

CREATE SERVER eu2_srv
  FOREIGN DATA WRAPPER ogr_fdw
  OPTIONS (
    datasource 'MSSQL:server=eu-prd2-sqlsrv-ee-db01.czz1yneu9gmr.eu-central-1.rds.amazonaws.com,1433;database=EU-SurveyorProduction2;uid=dsoler;pwd=2twN2cY0uIwm;driver=FreeTDS',
    format 'MSSQLSpatial',
    config_options 'MSSQLSPATIAL_LIST_ALL_TABLES=YES MSSQLSPATIAL_USE_GEOMETRY_COLUMNS=NO'
  );

IMPORT FOREIGN SCHEMA ogr_all
  LIMIT TO (
    "dbo.Customer",
    "dbo.Report",
    "dbo.ReportLabel",
    "dbo.Label",
    "dbo.ReportType",
    "dbo.ReportArea",
    "dbo.ReportCompliance",
    "dbo.ReportAreaCovered",
    "dbo.EmissionSource",
    "dbo.Survey",
    "dbo.ReportDrivingSurvey",
    "dbo.SurveyQACheck",
    "dbo.Segment",
    "dbo.SurveyorUnit"
  )
  FROM SERVER eu1_srv
  INTO eu1
  OPTIONS (
    launder_table_names 'false',
    launder_column_names 'false'
  );

DO $$
DECLARE
  r record;
BEGIN
  FOR r IN
    SELECT foreign_table_name
    FROM information_schema.foreign_tables
    WHERE foreign_table_schema = 'eu1'
      AND foreign_table_name LIKE 'dbo.%'
  LOOP
    EXECUTE format(
      'ALTER FOREIGN TABLE eu1.%I RENAME TO %I',
      r.foreign_table_name,
      substr(r.foreign_table_name, 5)
    );
  END LOOP;
END $$;

IMPORT FOREIGN SCHEMA ogr_all
  LIMIT TO (
    "dbo.Customer",
    "dbo.Report",
    "dbo.ReportLabel",
    "dbo.Label",
    "dbo.ReportType",
    "dbo.ReportArea",
    "dbo.ReportCompliance",
    "dbo.ReportAreaCovered",
    "dbo.EmissionSource",
    "dbo.Survey",
    "dbo.ReportDrivingSurvey",
    "dbo.SurveyQACheck",
    "dbo.Segment",
    "dbo.SurveyorUnit"
  )
  FROM SERVER eu2_srv
  INTO eu2
  OPTIONS (
    launder_table_names 'false',
    launder_column_names 'false'
  );

DO $$
DECLARE
  r record;
BEGIN
  FOR r IN
    SELECT foreign_table_name
    FROM information_schema.foreign_tables
    WHERE foreign_table_schema = 'eu2'
      AND foreign_table_name LIKE 'dbo.%'
  LOOP
    EXECUTE format(
      'ALTER FOREIGN TABLE eu2.%I RENAME TO %I',
      r.foreign_table_name,
      substr(r.foreign_table_name, 5)
    );
  END LOOP;
END $$;

SELECT foreign_table_schema, foreign_table_name
FROM information_schema.foreign_tables
WHERE foreign_table_schema IN ('eu1', 'eu2')
ORDER BY 1, 2;

SELECT 'eu1.Report' AS target, COUNT(*) AS rows FROM eu1."Report";
SELECT column_name, udt_name
FROM information_schema.columns
WHERE table_schema = 'eu1' AND table_name = 'ReportArea'
ORDER BY ordinal_position;
