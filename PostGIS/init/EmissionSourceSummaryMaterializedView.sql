-- Emission source summary snapshot tables mirroring
-- lib/ingester/EmissionSourceSummaryIngester.py
--
-- Aggregates eu1/eu2."EmissionSource" per ReportId for reports already present in
-- kpihub."MV_ReportSummary_eu1" / kpihub."MV_ReportSummary_eu2".
--
-- Prerequisite:
--   1. psql ... -f IngesterTables.sql
--   2. psql ... -f SeedCustomerInfo.sql
--   3. psql ... -f ReportSummaryMaterializedView.sql
--   4. CALL kpihub.refresh_report_summary();
--
-- Setup:
--   psql -U dsoler -d Datanalytics -v ON_ERROR_STOP=1 -f EmissionSourceSummaryMaterializedView.sql
--
-- Load / refresh data:
--   CALL kpihub.refresh_emission_source_summary();

SET enable_mergejoin = off;
SET work_mem = '256MB';
SET maintenance_work_mem = '512MB';

DROP VIEW IF EXISTS kpihub."V_EmissionSourceSummary";
DROP TABLE IF EXISTS kpihub."MV_EmissionSourceSummary_eu1";
DROP TABLE IF EXISTS kpihub."MV_EmissionSourceSummary_eu2";

CREATE TABLE kpihub."MV_EmissionSourceSummary_eu1" (
  "ReportId" uuid PRIMARY KEY,
  "EmissionRate" double precision,
  "EmissionRateLPM" double precision,
  "RepresentativeEmissionRate" double precision,
  "RepresentativeEmissionRateLPM" double precision,
  "LisaCount" integer,
  "B0Count" integer,
  "B1Count" integer,
  "Bm1Count" integer,
  "Bm2Count" integer,
  "B0RepEmissionRateLPM" double precision,
  "B1RepEmissionRateLPM" double precision,
  "Bm1RepEmissionRateLPM" double precision,
  "Bm2RepEmissionRateLPM" double precision,
  "B0RepEmissionRate" double precision,
  "B1RepEmissionRate" double precision,
  "Bm1RepEmissionRate" double precision,
  "Bm2RepEmissionRate" double precision,
  "Not_NGCount" integer,
  "PGCount" integer,
  "NGCount" integer,
  "LastUpdated" timestamp
);

CREATE TABLE kpihub."MV_EmissionSourceSummary_eu2" (
  LIKE kpihub."MV_EmissionSourceSummary_eu1" INCLUDING ALL
);

CREATE OR REPLACE PROCEDURE kpihub.refresh_emission_source_summary_customer(
  p_customer_id uuid,
  p_db_location text
)
LANGUAGE plpgsql
AS $$
DECLARE
  lsdb_schema text;
  report_table text;
  target_table text;
BEGIN
  IF upper(p_db_location) = 'EU2' THEN
    lsdb_schema := 'eu2';
    report_table := 'kpihub."MV_ReportSummary_eu2"';
    target_table := 'kpihub."MV_EmissionSourceSummary_eu2"';
  ELSIF upper(p_db_location) = 'EU1' THEN
    lsdb_schema := 'eu1';
    report_table := 'kpihub."MV_ReportSummary_eu1"';
    target_table := 'kpihub."MV_EmissionSourceSummary_eu1"';
  ELSE
    RAISE EXCEPTION 'Unsupported DB location: % (expected EU1 or EU2)', p_db_location;
  END IF;

  EXECUTE format(
    $sql$
    DELETE FROM %s
    WHERE "ReportId" IN (
      SELECT "ReportId"
      FROM %s
      WHERE "CustomerId" = $1
    )
    $sql$,
    target_table,
    report_table
  ) USING p_customer_id;

  EXECUTE format(
    $sql$
    INSERT INTO %s (
      "ReportId",
      "EmissionRate",
      "EmissionRateLPM",
      "RepresentativeEmissionRate",
      "RepresentativeEmissionRateLPM",
      "LisaCount",
      "B0Count",
      "B1Count",
      "Bm1Count",
      "Bm2Count",
      "B0RepEmissionRateLPM",
      "B1RepEmissionRateLPM",
      "Bm1RepEmissionRateLPM",
      "Bm2RepEmissionRateLPM",
      "B0RepEmissionRate",
      "B1RepEmissionRate",
      "Bm1RepEmissionRate",
      "Bm2RepEmissionRate",
      "Not_NGCount",
      "PGCount",
      "NGCount",
      "LastUpdated"
    )
    SELECT
      ES."ReportId",
      COALESCE(SUM(ES."EmissionRate") FILTER (
        WHERE ES."Disposition" IS NULL OR ES."Disposition" <> 2
      ), 0) AS "EmissionRate",
      COALESCE(SUM(ES."EmissionRate") FILTER (
        WHERE ES."Disposition" IS NULL OR ES."Disposition" <> 2
      ), 0) * 0.471947 AS "EmissionRateLPM",
      COALESCE(SUM(ES."RepresentativeEmissionRate") FILTER (
        WHERE ES."Disposition" IS NULL OR ES."Disposition" <> 2
      ), 0) AS "RepresentativeEmissionRate",
      COALESCE(SUM(ES."RepresentativeEmissionRate") FILTER (
        WHERE ES."Disposition" IS NULL OR ES."Disposition" <> 2
      ), 0) * 0.471947 AS "RepresentativeEmissionRateLPM",
      COUNT(ES."Id") FILTER (
        WHERE ES."Disposition" IS NULL OR ES."Disposition" <> 2
      )::integer AS "LisaCount",
      COUNT(*) FILTER (
        WHERE (ES."Disposition" IS NULL OR ES."Disposition" <> 2)
          AND ES."RepresentativeBinLabel" = 'B0'
      )::integer AS "B0Count",
      COUNT(*) FILTER (
        WHERE (ES."Disposition" IS NULL OR ES."Disposition" <> 2)
          AND ES."RepresentativeBinLabel" = 'B1'
      )::integer AS "B1Count",
      COUNT(*) FILTER (
        WHERE (ES."Disposition" IS NULL OR ES."Disposition" <> 2)
          AND ES."RepresentativeBinLabel" = 'B-1'
      )::integer AS "Bm1Count",
      COUNT(*) FILTER (
        WHERE (ES."Disposition" IS NULL OR ES."Disposition" <> 2)
          AND ES."RepresentativeBinLabel" = 'B-2'
      )::integer AS "Bm2Count",
      COALESCE(SUM(ES."RepresentativeEmissionRate") FILTER (
        WHERE (ES."Disposition" IS NULL OR ES."Disposition" <> 2)
          AND ES."RepresentativeBinLabel" = 'B0'
      ), 0) * 0.471947 AS "B0RepEmissionRateLPM",
      COALESCE(SUM(ES."RepresentativeEmissionRate") FILTER (
        WHERE (ES."Disposition" IS NULL OR ES."Disposition" <> 2)
          AND ES."RepresentativeBinLabel" = 'B1'
      ), 0) * 0.471947 AS "B1RepEmissionRateLPM",
      COALESCE(SUM(ES."RepresentativeEmissionRate") FILTER (
        WHERE (ES."Disposition" IS NULL OR ES."Disposition" <> 2)
          AND ES."RepresentativeBinLabel" = 'B-1'
      ), 0) * 0.471947 AS "Bm1RepEmissionRateLPM",
      COALESCE(SUM(ES."RepresentativeEmissionRate") FILTER (
        WHERE (ES."Disposition" IS NULL OR ES."Disposition" <> 2)
          AND ES."RepresentativeBinLabel" = 'B-2'
      ), 0) * 0.471947 AS "Bm2RepEmissionRateLPM",
      COALESCE(SUM(ES."RepresentativeEmissionRate") FILTER (
        WHERE (ES."Disposition" IS NULL OR ES."Disposition" <> 2)
          AND ES."RepresentativeBinLabel" = 'B0'
      ), 0) AS "B0RepEmissionRate",
      COALESCE(SUM(ES."RepresentativeEmissionRate") FILTER (
        WHERE (ES."Disposition" IS NULL OR ES."Disposition" <> 2)
          AND ES."RepresentativeBinLabel" = 'B1'
      ), 0) AS "B1RepEmissionRate",
      COALESCE(SUM(ES."RepresentativeEmissionRate") FILTER (
        WHERE (ES."Disposition" IS NULL OR ES."Disposition" <> 2)
          AND ES."RepresentativeBinLabel" = 'B-1'
      ), 0) AS "Bm1RepEmissionRate",
      COALESCE(SUM(ES."RepresentativeEmissionRate") FILTER (
        WHERE (ES."Disposition" IS NULL OR ES."Disposition" <> 2)
          AND ES."RepresentativeBinLabel" = 'B-2'
      ), 0) AS "Bm2RepEmissionRate",
      COUNT(*) FILTER (WHERE ES."Disposition" = 2)::integer AS "Not_NGCount",
      COUNT(*) FILTER (WHERE ES."Disposition" = 3)::integer AS "PGCount",
      COUNT(*) FILTER (WHERE ES."Disposition" = 1)::integer AS "NGCount",
      NOW() AS "LastUpdated"
    FROM %I."EmissionSource" ES
    WHERE ES."ReportId" IN (
      SELECT "ReportId"
      FROM %s
      WHERE "CustomerId" = $1
    )
    GROUP BY ES."ReportId"
    $sql$,
    target_table,
    lsdb_schema,
    report_table
  ) USING p_customer_id;
END;
$$;

CREATE OR REPLACE PROCEDURE kpihub.refresh_emission_source_summary()
LANGUAGE plpgsql
AS $$
DECLARE
  cust record;
BEGIN
  SET LOCAL enable_mergejoin = off;

  TRUNCATE TABLE kpihub."MV_EmissionSourceSummary_eu1";
  TRUNCATE TABLE kpihub."MV_EmissionSourceSummary_eu2";

  FOR cust IN
    SELECT customerid, dblocation
    FROM kpihub."KPI_Customer"
    WHERE active IS TRUE
      AND dblocation IS NOT NULL
      AND upper(dblocation) IN ('EU1', 'EU2')
    ORDER BY "Name"
  LOOP
    CALL kpihub.refresh_emission_source_summary_customer(
      cust.customerid,
      cust.dblocation
    );
  END LOOP;
END;
$$;

CREATE VIEW kpihub."V_EmissionSourceSummary" AS
SELECT * FROM kpihub."MV_EmissionSourceSummary_eu1"
UNION ALL
SELECT * FROM kpihub."MV_EmissionSourceSummary_eu2";

COMMENT ON TABLE kpihub."MV_EmissionSourceSummary_eu1" IS
  'EU1 emission source summary per report for active KPI_Customer rows. Refresh via CALL kpihub.refresh_emission_source_summary().';

COMMENT ON TABLE kpihub."MV_EmissionSourceSummary_eu2" IS
  'EU2 emission source summary per report for active KPI_Customer rows. Refresh via CALL kpihub.refresh_emission_source_summary().';

COMMENT ON PROCEDURE kpihub.refresh_emission_source_summary() IS
  'Reload emission source summary tables for active customers. Requires report summary MVs to be refreshed first.';
