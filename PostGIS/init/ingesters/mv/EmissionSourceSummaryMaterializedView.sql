-- Emission source summary snapshot tables mirroring
-- lib/ingester/EmissionSourceSummaryIngester.py
--
-- Aggregates eu1/eu2."EmissionSource" per ReportId for every report in
-- kpihub."MV_ReportSummary_eu1" / kpihub."MV_ReportSummary_eu2". Reports with
-- no emission sources are inserted with zero-valued metrics.
--
-- Prerequisite:
--   1. psql ... -f IngesterTables.sql
--   2. psql ... -f SeedCustomerInfo.sql
--   3. psql ... -f ReportSummary.sql + REFRESH MATERIALIZED VIEW on MV_ReportSummary_eu1/eu2
--
-- Setup:
--   psql -U dsoler -d Datanalytics -v ON_ERROR_STOP=1 -f EmissionSourceSummaryMaterializedView.sql
--
-- Load / refresh data:
--   CALL kpihub.refresh_emission_source_summary();
--   CALL kpihub.refresh_emission_source_summary_region('EU1');
--   CALL kpihub.refresh_emission_source_summary_customer('<customer-id>'::uuid, 'EU1');

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

CREATE OR REPLACE PROCEDURE kpihub.refresh_emission_source_summary_load(
  p_db_location text,
  p_customer_id uuid DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
DECLARE
  lsdb_schema text;
  report_table text;
  target_table text;
BEGIN
  SET LOCAL enable_mergejoin = off;
  SET LOCAL work_mem = '1GB';

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
    WITH report_scope AS (
      SELECT R."ReportId"
      FROM %s R
      WHERE ($1::uuid IS NULL OR R."CustomerId" = $1)
    ),
    emission_agg AS (
      SELECT
        ES."ReportId"::uuid AS "ReportId",
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
        COUNT(*) FILTER (WHERE ES."Disposition" = 1)::integer AS "NGCount"
      FROM %I."EmissionSource" ES
      INNER JOIN report_scope rs
        ON upper(ES."ReportId") = upper(rs."ReportId"::text)
      GROUP BY ES."ReportId"::uuid
    )
    SELECT
      rs."ReportId",
      COALESCE(ea."EmissionRate", 0) AS "EmissionRate",
      COALESCE(ea."EmissionRateLPM", 0) AS "EmissionRateLPM",
      COALESCE(ea."RepresentativeEmissionRate", 0) AS "RepresentativeEmissionRate",
      COALESCE(ea."RepresentativeEmissionRateLPM", 0) AS "RepresentativeEmissionRateLPM",
      COALESCE(ea."LisaCount", 0) AS "LisaCount",
      COALESCE(ea."B0Count", 0) AS "B0Count",
      COALESCE(ea."B1Count", 0) AS "B1Count",
      COALESCE(ea."Bm1Count", 0) AS "Bm1Count",
      COALESCE(ea."Bm2Count", 0) AS "Bm2Count",
      COALESCE(ea."B0RepEmissionRateLPM", 0) AS "B0RepEmissionRateLPM",
      COALESCE(ea."B1RepEmissionRateLPM", 0) AS "B1RepEmissionRateLPM",
      COALESCE(ea."Bm1RepEmissionRateLPM", 0) AS "Bm1RepEmissionRateLPM",
      COALESCE(ea."Bm2RepEmissionRateLPM", 0) AS "Bm2RepEmissionRateLPM",
      COALESCE(ea."B0RepEmissionRate", 0) AS "B0RepEmissionRate",
      COALESCE(ea."B1RepEmissionRate", 0) AS "B1RepEmissionRate",
      COALESCE(ea."Bm1RepEmissionRate", 0) AS "Bm1RepEmissionRate",
      COALESCE(ea."Bm2RepEmissionRate", 0) AS "Bm2RepEmissionRate",
      COALESCE(ea."Not_NGCount", 0) AS "Not_NGCount",
      COALESCE(ea."PGCount", 0) AS "PGCount",
      COALESCE(ea."NGCount", 0) AS "NGCount",
      NOW() AS "LastUpdated"
    FROM report_scope rs
    LEFT JOIN emission_agg ea ON ea."ReportId" = rs."ReportId"
    $sql$,
    target_table,
    report_table,
    lsdb_schema
  ) USING p_customer_id;
END;
$$;

CREATE OR REPLACE PROCEDURE kpihub.refresh_emission_source_summary_customer(
  p_customer_id uuid,
  p_db_location text
)
LANGUAGE plpgsql
AS $$
DECLARE
  report_table text;
  target_table text;
BEGIN
  IF upper(p_db_location) = 'EU2' THEN
    report_table := 'kpihub."MV_ReportSummary_eu2"';
    target_table := 'kpihub."MV_EmissionSourceSummary_eu2"';
  ELSIF upper(p_db_location) = 'EU1' THEN
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

  CALL kpihub.refresh_emission_source_summary_load(p_db_location, p_customer_id);
END;
$$;

CREATE OR REPLACE PROCEDURE kpihub.refresh_emission_source_summary_region(
  p_db_location text
)
LANGUAGE plpgsql
AS $$
DECLARE
  target_table text;
BEGIN
  IF upper(p_db_location) = 'EU2' THEN
    target_table := 'kpihub."MV_EmissionSourceSummary_eu2"';
  ELSIF upper(p_db_location) = 'EU1' THEN
    target_table := 'kpihub."MV_EmissionSourceSummary_eu1"';
  ELSE
    RAISE EXCEPTION 'Unsupported DB location: % (expected EU1 or EU2)', p_db_location;
  END IF;

  EXECUTE format('TRUNCATE TABLE %s', target_table);
  CALL kpihub.refresh_emission_source_summary_load(p_db_location, NULL);
END;
$$;

CREATE OR REPLACE PROCEDURE kpihub.refresh_emission_source_summary()
LANGUAGE plpgsql
AS $$
BEGIN
  -- One batched FDW pass per region (much faster than per-customer loops).
  CALL kpihub.refresh_emission_source_summary_region('EU1');
  CALL kpihub.refresh_emission_source_summary_region('EU2');
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
  'Reload emission source summaries in two batched passes (EU1 then EU2). Use refresh_emission_source_summary_customer for one customer.';

COMMENT ON PROCEDURE kpihub.refresh_emission_source_summary_region(text) IS
  'Truncate and reload one region table in a single batched FDW aggregation.';
