-- First-boot bootstrap for POSTGRES_DB (KPIHub_EU) only.
-- FDW, foreign tables, KPI schema, and migrations live under PostGIS/PSQL_routines/
-- and are NOT executed by Docker; run those SQL files manually with psql when needed.

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
CREATE EXTENSION IF NOT EXISTS postgres_fdw;
CREATE EXTENSION IF NOT EXISTS ogr_fdw;
CREATE EXTENSION IF NOT EXISTS tds_fdw;