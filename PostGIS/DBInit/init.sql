-- Run on first database initialization (docker-entrypoint-initdb.d)
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
CREATE EXTENSION IF NOT EXISTS postgis_tiger_geocoder;
CREATE EXTENSION IF NOT EXISTS postgres_fdw;
CREATE EXTENSION IF NOT EXISTS tds_fdw;

CREATE SCHEMA IF NOT EXISTS kpihub AUTHORIZATION dsoler;
CREATE SCHEMA IF NOT EXISTS eu1 AUTHORIZATION dsoler;
CREATE SCHEMA IF NOT EXISTS eu2 AUTHORIZATION dsoler;

-- EU1: locallib.picarrodb EU1_Conn (EUDBUSER / EUDBPW from .env)
CREATE SERVER IF NOT EXISTS eu1_srv
  FOREIGN DATA WRAPPER tds_fdw
  OPTIONS (
    servername 'eu-prd-sqlsrv-ee-db01.czz1yneu9gmr.eu-central-1.rds.amazonaws.com',
    port '1433',
    database 'EU-SurveyorProduction',
    tds_version '7.4'
  );

CREATE USER MAPPING IF NOT EXISTS FOR dsoler
  SERVER eu1_srv
  OPTIONS (username 'dsoler', password '2twN2cY0uIwm');

-- EU2: locallib.picarrodb EU2_Conn (EU2DBUSER / EU2DBPW from .env)
CREATE SERVER IF NOT EXISTS eu2_srv
  FOREIGN DATA WRAPPER tds_fdw
  OPTIONS (
    servername 'eu-prd2-sqlsrv-ee-db01.czz1yneu9gmr.eu-central-1.rds.amazonaws.com',
    port '1433',
    database 'EU-SurveyorProduction2',
    tds_version '7.4'
  );

CREATE USER MAPPING IF NOT EXISTS FOR dsoler
  SERVER eu2_srv
  OPTIONS (username 'dsoler', password '2twN2cY0uIwm');

-- KPIHub source tables (from lib/query/bank.py)
IMPORT FOREIGN SCHEMA dbo
  LIMIT TO (
    "Customer",
    "Report",
    "ReportLabel",
    "Label",
    "ReportType",
    "ReportArea",
    "ReportCompliance",
    "ReportAreaCovered",
    "EmissionSource",
    "Survey",
    "ReportDrivingSurvey",
    "SurveyQACheck",
    "Segment",
    "SurveyorUnit"
  )
  FROM SERVER eu1_srv
  INTO eu1;

IMPORT FOREIGN SCHEMA dbo
  LIMIT TO (
    "Customer",
    "Report",
    "ReportLabel",
    "Label",
    "ReportType",
    "ReportArea",
    "ReportCompliance",
    "ReportAreaCovered",
    "EmissionSource",
    "Survey",
    "ReportDrivingSurvey",
    "SurveyQACheck",
    "Segment",
    "SurveyorUnit"
  )
  FROM SERVER eu2_srv
  INTO eu2;

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
