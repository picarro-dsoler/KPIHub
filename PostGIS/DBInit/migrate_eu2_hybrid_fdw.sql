-- Hybrid FDW for EU2: tds_fdw for tabular MSSQL tables, ogr_fdw for ReportArea geometry.
--
-- Run on an existing database (after ogr_fdw eu2 import from init.sql / migrate_to_ogr_fdw.sql):
--   psql -h localhost -U dsoler -d Datanalytics -v ON_ERROR_STOP=1 \
--     -f KPIHub/PostGIS/DBInit/migrate_eu2_hybrid_fdw.sql
--
-- Verify:
--   SELECT foreign_table_schema, foreign_table_name
--     FROM information_schema.foreign_tables
--     WHERE foreign_table_schema IN ('eu2_tds', 'eu2_geo')
--     ORDER BY 1, 2;
--   SELECT COUNT(*) FROM eu2_tds."Report";
--   SELECT COUNT(*) FROM eu2_geo."ReportArea";

CREATE EXTENSION IF NOT EXISTS tds_fdw;

DROP SCHEMA IF EXISTS eu2_tds CASCADE;
DROP SCHEMA IF EXISTS eu2_geo CASCADE;

CREATE SCHEMA eu2_tds AUTHORIZATION dsoler;
CREATE SCHEMA eu2_geo AUTHORIZATION dsoler;

-- Tabular EU2 source (predicate pushdown for DateStarted, IN lists, etc.)
DROP SERVER IF EXISTS eu2_tds_srv CASCADE;

CREATE SERVER eu2_tds_srv
  FOREIGN DATA WRAPPER tds_fdw
  OPTIONS (
    servername 'eu-prd2-sqlsrv-ee-db01.czz1yneu9gmr.eu-central-1.rds.amazonaws.com',
    port '1433',
    database 'EU-SurveyorProduction2',
    tds_version '7.4'
  );

CREATE USER MAPPING FOR dsoler
  SERVER eu2_tds_srv
  OPTIONS (username 'dsoler', password '2twN2cY0uIwm');

IMPORT FOREIGN SCHEMA dbo
  LIMIT TO (
    "Customer",
    "Report",
    "ReportLabel",
    "Label",
    "ReportType",
    "ReportCompliance",
    "ReportAreaCovered"
  )
  FROM SERVER eu2_tds_srv
  INTO eu2_tds;

-- Geometry-only EU2 source (reuses existing ogr eu2_srv from init.sql)
IMPORT FOREIGN SCHEMA ogr_all
  LIMIT TO ("dbo.ReportArea")
  FROM SERVER eu2_srv
  INTO eu2_geo
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
    WHERE foreign_table_schema = 'eu2_geo'
      AND foreign_table_name LIKE 'dbo.%'
  LOOP
    EXECUTE format(
      'ALTER FOREIGN TABLE eu2_geo.%I RENAME TO %I',
      r.foreign_table_name,
      substr(r.foreign_table_name, 5)
    );
  END LOOP;
END $$;

SELECT foreign_table_schema, foreign_table_name
FROM information_schema.foreign_tables
WHERE foreign_table_schema IN ('eu2_tds', 'eu2_geo')
ORDER BY 1, 2;

SELECT 'eu2_tds.Report' AS target, COUNT(*) AS rows FROM eu2_tds."Report";
SELECT 'eu2_geo.ReportArea' AS target, COUNT(*) AS rows FROM eu2_geo."ReportArea";
