-- Run on first database initialization (docker-entrypoint-initdb.d)
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
CREATE EXTENSION IF NOT EXISTS postgis_tiger_geocoder;
CREATE EXTENSION IF NOT EXISTS postgres_fdw;
CREATE EXTENSION IF NOT EXISTS ogr_fdw;
CREATE EXTENSION IF NOT EXISTS tds_fdw;

CREATE SCHEMA IF NOT EXISTS kpihub AUTHORIZATION dsoler;
CREATE SCHEMA IF NOT EXISTS eu1 AUTHORIZATION dsoler;
CREATE SCHEMA IF NOT EXISTS eu2 AUTHORIZATION dsoler;

-- EU1: SQL Server via ogr_fdw (MSSQLSpatial handles geometry/geography columns)
-- Credentials are embedded in the datasource connection string (ogr_fdw has no user mapping).
CREATE SERVER IF NOT EXISTS eu1_srv
  FOREIGN DATA WRAPPER ogr_fdw
  OPTIONS (
    datasource 'MSSQL:server=eu-prd-sqlsrv-ee-db01.czz1yneu9gmr.eu-central-1.rds.amazonaws.com,1433;database=EU-SurveyorProduction;uid=dsoler;pwd=2twN2cY0uIwm;driver=FreeTDS',
    format 'MSSQLSpatial',
    config_options 'MSSQLSPATIAL_LIST_ALL_TABLES=YES MSSQLSPATIAL_USE_GEOMETRY_COLUMNS=NO'
  );

-- EU2: SQL Server via ogr_fdw
CREATE SERVER IF NOT EXISTS eu2_srv
  FOREIGN DATA WRAPPER ogr_fdw
  OPTIONS (
    datasource 'MSSQL:server=eu-prd2-sqlsrv-ee-db01.czz1yneu9gmr.eu-central-1.rds.amazonaws.com,1433;database=EU-SurveyorProduction2;uid=dsoler;pwd=2twN2cY0uIwm;driver=FreeTDS',
    format 'MSSQLSpatial',
    config_options 'MSSQLSPATIAL_LIST_ALL_TABLES=YES MSSQLSPATIAL_USE_GEOMETRY_COLUMNS=NO'
  );

-- ogr_fdw layer names are dbo.TableName; import via ogr_all then strip the dbo. prefix
-- so existing KPIHub SQL can keep using eu1."Report", etc.
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

-- EU2 hybrid: tds_fdw for tabular tables, ogr_fdw (eu2_srv) for ReportArea geometry only.
CREATE SCHEMA IF NOT EXISTS eu2_tds AUTHORIZATION dsoler;
CREATE SCHEMA IF NOT EXISTS eu2_geo AUTHORIZATION dsoler;

CREATE SERVER IF NOT EXISTS eu2_tds_srv
  FOREIGN DATA WRAPPER tds_fdw
  OPTIONS (
    servername 'eu-prd2-sqlsrv-ee-db01.czz1yneu9gmr.eu-central-1.rds.amazonaws.com',
    port '1433',
    database 'EU-SurveyorProduction2',
    tds_version '7.4'
  );

CREATE USER MAPPING IF NOT EXISTS FOR dsoler
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

-- DataHub: locallib.picarrodb DATAHUB_Conn (DATAHUBUSER / DATAHUBPW / DATAHUBDATABASE from .env)
CREATE SCHEMA IF NOT EXISTS dash AUTHORIZATION dsoler;

CREATE SERVER IF NOT EXISTS datahub_srv
  FOREIGN DATA WRAPPER postgres_fdw
  OPTIONS (
    host 'eu-sensebird-migrated-rds-pg1-r4-prd.czz1yneu9gmr.eu-central-1.rds.amazonaws.com',
    port '5432',
    dbname 'datahub',
    sslmode 'require'
  );

CREATE USER MAPPING IF NOT EXISTS FOR dsoler
  SERVER datahub_srv
  OPTIONS (user 'dmauro', password 'Hub&?Dat64');

-- KPIHub DataHub source (from lib/query/bank.py)
IMPORT FOREIGN SCHEMA dash
  LIMIT TO (v_report)
  FROM SERVER datahub_srv
  INTO dash;
