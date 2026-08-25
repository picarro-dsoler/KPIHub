-- Report summary snapshot tables mirroring lib/ingester/ReportSummaryIngester.py
--
-- These are regular TABLES (not PostgreSQL materialized views). Query them via:
--   \dt kpihub."MV_ReportSummary_*"
--   SELECT * FROM kpihub."V_ReportSummary";
--
-- Incremental sync pulls only new / recently started reports from eu1/eu2 FDW
-- tables instead of rebuilding the full snapshot on every run.
--
-- Prerequisite:
--   1. IngesterTables.sql, SeedCustomerInfo.sql
--
-- Setup:
--   psql -U dsoler -d Datanalytics -v ON_ERROR_STOP=1 -f ReportSummary.sql
--
-- Refresh (incremental by default; optional since_date for backfill):
--   CALL kpihub.refresh_report_summary_customer('<customer-id>'::uuid, 'EU1');
--   CALL kpihub.refresh_report_summary_customer('<customer-id>'::uuid, 'EU1', DATE '2023-01-01');
--   CALL kpihub.refresh_report_summary_region('EU1');
--   CALL kpihub.refresh_report_summary();

SET enable_mergejoin = off;
SET work_mem = '256MB';
SET maintenance_work_mem = '512MB';

DROP VIEW IF EXISTS kpihub."V_KPIReportSummary";
DROP VIEW IF EXISTS kpihub."V_ReportSummary";
DROP TABLE IF EXISTS kpihub."MV_KPIReportSummary_eu1";
DROP TABLE IF EXISTS kpihub."MV_KPIReportSummary_eu2";

DROP PROCEDURE IF EXISTS kpihub.refresh_KPIReportSummary();
DROP PROCEDURE IF EXISTS kpihub.refresh_KPIReportSummary_region(text, date);
DROP PROCEDURE IF EXISTS kpihub.refresh_KPIReportSummary_customer(uuid, text, date);

CREATE TABLE kpihub."MV_KPIReportSummary_eu1" (
  "ReportId" uuid PRIMARY KEY,
  "CustomerId" uuid NOT NULL,
  "ReportName" text,
  "ReportDate" timestamp,
  "ReportYear" integer,
  "ReportMonth" integer,
  "ReportWeek" integer,
  "ReportAssetLengthKm" double precision,
  "AssetCoveredLengthKm" double precision,
  "DistributionPipeKm" double precision,
  "DistributionPipeCoveredKm" double precision,
  "ServicePipeKm" double precision,
  "ServicePipeCoveredKm" double precision,
  "BoundaryName" text,
  "BoundaryType" text,
  "BoundaryMode" text,
  "BoundaryPlant" text,
  "BoundarySubplant" text,
  "BoundaryRegion" text,
  "BoundarySubRegion" text,
  "ReportArea" geometry,
  "LastUpdated" timestamp
);

CREATE TABLE kpihub."MV_KPIReportSummary_eu2" (
  LIKE kpihub."MV_ReportSummary_eu1" INCLUDING ALL
);

CREATE INDEX IF NOT EXISTS "MV_KPIReportSummary_eu1_CustomerId_idx"
  ON kpihub."MV_KPIReportSummary_eu1" ("CustomerId");

CREATE INDEX IF NOT EXISTS "MV_KPIReportSummary_eu2_CustomerId_idx"
  ON kpihub."MV_KPIReportSummary_eu2" ("CustomerId");

CREATE INDEX IF NOT EXISTS "MV_KPIReportSummary_eu1_ReportDate_idx"
  ON kpihub."MV_KPIReportSummary_eu1" ("ReportDate");

CREATE INDEX IF NOT EXISTS "MV_KPIReportSummary_eu2_ReportDate_idx"
  ON kpihub."MV_KPIReportSummary_eu2" ("ReportDate");

CREATE INDEX IF NOT EXISTS "MV_KPIReportSummary_eu1_ReportArea_gix"
  ON kpihub."MV_KPIReportSummary_eu1" USING GIST ("ReportArea");

CREATE INDEX IF NOT EXISTS "MV_KPIReportSummary_eu2_ReportArea_gix"
  ON kpihub."MV_KPIReportSummary_eu2" USING GIST ("ReportArea");

DROP FUNCTION IF EXISTS kpihub.get_new_reports_after_last_date(text, text);

CREATE OR REPLACE FUNCTION kpihub.get_new_reports_after_last_date(
    p_schema text,
    p_mv_table text
)
RETURNS TABLE (
    "ReportId" uuid,
    "CustomerId" uuid,
    "ReportName" text,
    "ReportDate" timestamp,
    "ReportYear" integer,
    "ReportMonth" integer,
    "ReportWeek" integer,
    "ReportAssetLengthKm" double precision,
    "AssetCoveredLengthKm" double precision,
    "DistributionPipeKm" double precision,
    "DistributionPipeCoveredKm" double precision,
    "ServicePipeKm" double precision,
    "ServicePipeCoveredKm" double precision,
    "BoundaryName" text,
    "BoundaryType" text,
    "BoundaryMode" text,
    "BoundaryPlant" text,
    "BoundarySubplant" text,
    "BoundaryRegion" text,
    "BoundarySubRegion" text,
    "ReportArea" geometry,
    "LastUpdated" timestamp
)
LANGUAGE plpgsql
AS $func$
DECLARE
    sql text;
    last_report_date timestamp;
    has_new_reports boolean;
BEGIN
    -- Resolve cutoff locally (fast index scan on MV table).
    EXECUTE format(
        'SELECT COALESCE(MAX("ReportDate"), ''2023-01-01''::timestamp) FROM kpihub.%I',
        p_mv_table
    )
    INTO last_report_date;

    -- Cheap probe: literal date in SQL so ogr_fdw can push "DateStarted > ..." to MSSQL.
    -- Parameters ($1) and AT TIME ZONE in WHERE prevent pushdown → full remote scan.
    EXECUTE format(
        'SELECT EXISTS (
            SELECT 1
            FROM %I."Report" R
            WHERE R."DateStarted" > %L::timestamp
            LIMIT 1
        )',
        p_schema,
        last_report_date
    )
    INTO has_new_reports;

    IF NOT has_new_reports THEN
        RETURN;
    END IF;

    sql :=
    'SELECT
        R."Id"::uuid AS "ReportId",
        C."Id"::uuid AS "CustomerId",
        CASE
            WHEN RT."Description" = ''Compliance'' THEN ''CR-'' || SUBSTRING(R."Id"::text, 1, 6)
            WHEN RT."Description" = ''Emissions'' THEN ''ER-'' || SUBSTRING(R."Id"::text, 1, 6)
            ELSE ''CR-'' || SUBSTRING(R."Id"::text, 1, 6)
        END::text AS "ReportName",
        (R."DateStarted" AT TIME ZONE ''UTC'')::timestamp AS "ReportDate",
        EXTRACT(YEAR FROM (R."DateStarted" AT TIME ZONE ''UTC''))::int AS "ReportYear",
        EXTRACT(MONTH FROM (R."DateStarted" AT TIME ZONE ''UTC''))::int AS "ReportMonth",
        EXTRACT(WEEK FROM (R."DateStarted" AT TIME ZONE ''UTC''))::int AS "ReportWeek",
        RAC."AssetLengthKM" AS "ReportAssetLengthKm",
        RAC."AssetLengthKM" * RC."PercentCoverageAssets" AS "AssetCoveredLengthKm",
        RAC."DistributionPipeKm",
        RAC."DistributionPipeCoveredKm",
        RAC."ServicePipeKm",
        RAC."ServicePipeCoveredKm",
        dh.bo_name::text AS "BoundaryName",
        dh.bo_type::text AS "BoundaryType",
        dh.bo_mode::text AS "BoundaryMode",
        dh.bo_plant::text AS "BoundaryPlant",
        dh.bo_subplant::text AS "BoundarySubplant",
        dh.bo_region::text AS "BoundaryRegion",
        dh.bo_subregion::text AS "BoundarySubRegion",
        RA."Shape" AS "ReportArea",
        (NOW() AT TIME ZONE ''UTC'')::timestamp AS "LastUpdated"
    FROM (
        SELECT *
        FROM "' || p_schema || '"."Report"
        WHERE "DateStarted" > ' || quote_literal(last_report_date) || '::timestamp
    ) R
    INNER JOIN "' || p_schema || '"."Customer" C ON R."CustomerId" = C."Id"
    INNER JOIN "' || p_schema || '"."ReportLabel" RL ON R."Id" = RL."ReportId"
    INNER JOIN "' || p_schema || '"."Label" L ON RL."LabelId" = L."Id"
    LEFT JOIN "' || p_schema || '"."ReportType" RT ON R."ReportTypeId" = RT."Id"
    LEFT JOIN "' || p_schema || '"."ReportCompliance" RC ON R."Id" = RC."ReportId"
    LEFT JOIN "' || p_schema || '"."ReportAreaCovered" RAC ON R."Id" = RAC."ReportId"
    LEFT JOIN "' || p_schema || '"."ReportArea" RA ON R."Id" = RA."ReportId"
    LEFT JOIN dash.v_report dh ON dh.rp_id = R."Id"::uuid
    WHERE L."Title" = ''Final Checkbox''
      AND RL."IsActive" = ''1''';

    RETURN QUERY EXECUTE sql;
END;
$func$;

COMMENT ON FUNCTION kpihub.get_new_reports_after_last_date(text, text) IS
  'Returns Final Checkbox reports newer than the latest ReportDate in the target MV table (UTC timestamps).';

CREATE OR REPLACE PROCEDURE kpihub.refresh_report_summary_customer(
  p_customer_id uuid,
  p_db_location text,
  p_since_date date DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
DECLARE
  lsdb_schema text;
  target_table text;
  min_start_date date;
  since_date date;
  has_data boolean;
BEGIN
  SET LOCAL enable_mergejoin = off;
  SET LOCAL work_mem = '1GB';

  IF upper(p_db_location) = 'EU2' THEN
    lsdb_schema := 'eu2';
    target_table := 'kpihub."MV_ReportSummary_eu2"';
    min_start_date := DATE '2023-01-01';
  ELSIF upper(p_db_location) = 'EU1' THEN
    lsdb_schema := 'eu1';
    target_table := 'kpihub."MV_ReportSummary_eu1"';
    min_start_date := DATE '2023-01-01';
  ELSE
    RAISE EXCEPTION 'Unsupported DB location: % (expected EU1 or EU2)', p_db_location;
  END IF;

  since_date := p_since_date;
  IF since_date IS NULL THEN
    EXECUTE format(
      'SELECT EXISTS (SELECT 1 FROM %s WHERE "CustomerId" = $1 LIMIT 1)',
      target_table
    )
    INTO has_data
    USING p_customer_id;

    IF has_data THEN
      -- Mirrors SQLite UPDATE_WINDOW_DAYS = 1 in lib/config.py
      since_date := CURRENT_DATE - 1;
    ELSE
      since_date := min_start_date;
    END IF;
  END IF;

  IF since_date <= min_start_date THEN
    EXECUTE format(
      $sql$
      INSERT INTO %s (
        "ReportId",
        "CustomerId",
        "ReportName",
        "ReportDate",
        "ReportYear",
        "ReportMonth",
        "ReportWeek",
        "ReportAssetLengthKm",
        "AssetCoveredLengthKm",
        "DistributionPipeKm",
        "DistributionPipeCoveredKm",
        "ServicePipeKm",
        "ServicePipeCoveredKm",
        "BoundaryName",
        "BoundaryType",
        "BoundaryMode",
        "BoundaryPlant",
        "BoundarySubplant",
        "BoundaryRegion",
        "BoundarySubRegion",
        "ReportArea",
        "LastUpdated"
      )
      SELECT
        R."Id"::uuid AS "ReportId",
        C."Id"::uuid AS "CustomerId",
        CASE
          WHEN RT."Description" = 'Compliance' THEN 'CR-' || SUBSTRING(R."Id"::text, 1, 6)
          WHEN RT."Description" = 'Emissions' THEN 'ER-' || SUBSTRING(R."Id"::text, 1, 6)
          ELSE 'CR-' || SUBSTRING(R."Id"::text, 1, 6)
        END AS "ReportName",
        R."DateStarted" AS "ReportDate",
        EXTRACT(YEAR FROM R."DateStarted")::int AS "ReportYear",
        EXTRACT(MONTH FROM R."DateStarted")::int AS "ReportMonth",
        EXTRACT(WEEK FROM R."DateStarted")::int AS "ReportWeek",
        RAC."AssetLengthKM" AS "ReportAssetLengthKm",
        RAC."AssetLengthKM" * RC."PercentCoverageAssets" AS "AssetCoveredLengthKm",
        RAC."DistributionPipeKm",
        RAC."DistributionPipeCoveredKm",
        RAC."ServicePipeKm",
        RAC."ServicePipeCoveredKm",
        dh.bo_name AS "BoundaryName",
        dh.bo_type AS "BoundaryType",
        dh.bo_mode AS "BoundaryMode",
        dh.bo_plant AS "BoundaryPlant",
        dh.bo_subplant AS "BoundarySubplant",
        dh.bo_region AS "BoundaryRegion",
        dh.bo_subregion AS "BoundarySubRegion",
        RA."Shape" AS "ReportArea",
        NOW() AS "LastUpdated"
      FROM %I."Report" R
      INNER JOIN %I."Customer" C ON R."CustomerId" = C."Id"
      LEFT JOIN %I."ReportLabel" RL ON R."Id" = RL."ReportId"
      LEFT JOIN %I."Label" L ON RL."LabelId" = L."Id"
      LEFT JOIN %I."ReportType" RT ON R."ReportTypeId" = RT."Id"
      LEFT JOIN %I."ReportCompliance" RC ON R."Id" = RC."ReportId"
      LEFT JOIN %I."ReportAreaCovered" RAC ON R."Id" = RAC."ReportId"
      LEFT JOIN %I."ReportArea" RA ON R."Id" = RA."ReportId"
      LEFT JOIN dash.v_report dh ON dh.rp_id = R."Id"::uuid
      WHERE C."Id"::uuid = $1
        AND L."Title" = 'Final Checkbox'
        AND RL."IsActive" = '1'
        AND R."DateStarted" >= $2
      ON CONFLICT ("ReportId") DO UPDATE SET
        "CustomerId" = EXCLUDED."CustomerId",
        "ReportName" = EXCLUDED."ReportName",
        "ReportDate" = EXCLUDED."ReportDate",
        "ReportYear" = EXCLUDED."ReportYear",
        "ReportMonth" = EXCLUDED."ReportMonth",
        "ReportWeek" = EXCLUDED."ReportWeek",
        "ReportAssetLengthKm" = EXCLUDED."ReportAssetLengthKm",
        "AssetCoveredLengthKm" = EXCLUDED."AssetCoveredLengthKm",
        "DistributionPipeKm" = EXCLUDED."DistributionPipeKm",
        "DistributionPipeCoveredKm" = EXCLUDED."DistributionPipeCoveredKm",
        "ServicePipeKm" = EXCLUDED."ServicePipeKm",
        "ServicePipeCoveredKm" = EXCLUDED."ServicePipeCoveredKm",
        "BoundaryName" = EXCLUDED."BoundaryName",
        "BoundaryType" = EXCLUDED."BoundaryType",
        "BoundaryMode" = EXCLUDED."BoundaryMode",
        "BoundaryPlant" = EXCLUDED."BoundaryPlant",
        "BoundarySubplant" = EXCLUDED."BoundarySubplant",
        "BoundaryRegion" = EXCLUDED."BoundaryRegion",
        "BoundarySubRegion" = EXCLUDED."BoundarySubRegion",
        "ReportArea" = EXCLUDED."ReportArea",
        "LastUpdated" = EXCLUDED."LastUpdated"
      $sql$,
      target_table,
      lsdb_schema, lsdb_schema, lsdb_schema, lsdb_schema, lsdb_schema,
      lsdb_schema, lsdb_schema, lsdb_schema
    ) USING p_customer_id, min_start_date;
  ELSE
    EXECUTE format(
      $sql$
      INSERT INTO %s (
        "ReportId",
        "CustomerId",
        "ReportName",
        "ReportDate",
        "ReportYear",
        "ReportMonth",
        "ReportWeek",
        "ReportAssetLengthKm",
        "AssetCoveredLengthKm",
        "DistributionPipeKm",
        "DistributionPipeCoveredKm",
        "ServicePipeKm",
        "ServicePipeCoveredKm",
        "BoundaryName",
        "BoundaryType",
        "BoundaryMode",
        "BoundaryPlant",
        "BoundarySubplant",
        "BoundaryRegion",
        "BoundarySubRegion",
        "ReportArea",
        "LastUpdated"
      )
      SELECT
        R."Id"::uuid AS "ReportId",
        C."Id"::uuid AS "CustomerId",
        CASE
          WHEN RT."Description" = 'Compliance' THEN 'CR-' || SUBSTRING(R."Id"::text, 1, 6)
          WHEN RT."Description" = 'Emissions' THEN 'ER-' || SUBSTRING(R."Id"::text, 1, 6)
          ELSE 'CR-' || SUBSTRING(R."Id"::text, 1, 6)
        END AS "ReportName",
        R."DateStarted" AS "ReportDate",
        EXTRACT(YEAR FROM R."DateStarted")::int AS "ReportYear",
        EXTRACT(MONTH FROM R."DateStarted")::int AS "ReportMonth",
        EXTRACT(WEEK FROM R."DateStarted")::int AS "ReportWeek",
        RAC."AssetLengthKM" AS "ReportAssetLengthKm",
        RAC."AssetLengthKM" * RC."PercentCoverageAssets" AS "AssetCoveredLengthKm",
        RAC."DistributionPipeKm",
        RAC."DistributionPipeCoveredKm",
        RAC."ServicePipeKm",
        RAC."ServicePipeCoveredKm",
        dh.bo_name AS "BoundaryName",
        dh.bo_type AS "BoundaryType",
        dh.bo_mode AS "BoundaryMode",
        dh.bo_plant AS "BoundaryPlant",
        dh.bo_subplant AS "BoundarySubplant",
        dh.bo_region AS "BoundaryRegion",
        dh.bo_subregion AS "BoundarySubRegion",
        RA."Shape" AS "ReportArea",
        NOW() AS "LastUpdated"
      FROM %I."Report" R
      INNER JOIN %I."Customer" C ON R."CustomerId" = C."Id"
      LEFT JOIN %I."ReportLabel" RL ON R."Id" = RL."ReportId"
      LEFT JOIN %I."Label" L ON RL."LabelId" = L."Id"
      LEFT JOIN %I."ReportType" RT ON R."ReportTypeId" = RT."Id"
      LEFT JOIN %I."ReportCompliance" RC ON R."Id" = RC."ReportId"
      LEFT JOIN %I."ReportAreaCovered" RAC ON R."Id" = RAC."ReportId"
      LEFT JOIN %I."ReportArea" RA ON R."Id" = RA."ReportId"
      LEFT JOIN dash.v_report dh ON dh.rp_id = R."Id"::uuid
      WHERE C."Id"::uuid = $1
        AND L."Title" = 'Final Checkbox'
        AND RL."IsActive" = '1'
        AND R."DateStarted" >= $2
      ON CONFLICT ("ReportId") DO UPDATE SET
        "CustomerId" = EXCLUDED."CustomerId",
        "ReportName" = EXCLUDED."ReportName",
        "ReportDate" = EXCLUDED."ReportDate",
        "ReportYear" = EXCLUDED."ReportYear",
        "ReportMonth" = EXCLUDED."ReportMonth",
        "ReportWeek" = EXCLUDED."ReportWeek",
        "ReportAssetLengthKm" = EXCLUDED."ReportAssetLengthKm",
        "AssetCoveredLengthKm" = EXCLUDED."AssetCoveredLengthKm",
        "DistributionPipeKm" = EXCLUDED."DistributionPipeKm",
        "DistributionPipeCoveredKm" = EXCLUDED."DistributionPipeCoveredKm",
        "ServicePipeKm" = EXCLUDED."ServicePipeKm",
        "ServicePipeCoveredKm" = EXCLUDED."ServicePipeCoveredKm",
        "BoundaryName" = EXCLUDED."BoundaryName",
        "BoundaryType" = EXCLUDED."BoundaryType",
        "BoundaryMode" = EXCLUDED."BoundaryMode",
        "BoundaryPlant" = EXCLUDED."BoundaryPlant",
        "BoundarySubplant" = EXCLUDED."BoundarySubplant",
        "BoundaryRegion" = EXCLUDED."BoundaryRegion",
        "BoundarySubRegion" = EXCLUDED."BoundarySubRegion",
        "ReportArea" = EXCLUDED."ReportArea",
        "LastUpdated" = EXCLUDED."LastUpdated"
      $sql$,
      target_table,
      lsdb_schema, lsdb_schema, lsdb_schema, lsdb_schema, lsdb_schema,
      lsdb_schema, lsdb_schema, lsdb_schema
    ) USING p_customer_id, since_date;

    EXECUTE format(
      $sql$
      INSERT INTO %s (
        "ReportId",
        "CustomerId",
        "ReportName",
        "ReportDate",
        "ReportYear",
        "ReportMonth",
        "ReportWeek",
        "ReportAssetLengthKm",
        "AssetCoveredLengthKm",
        "DistributionPipeKm",
        "DistributionPipeCoveredKm",
        "ServicePipeKm",
        "ServicePipeCoveredKm",
        "BoundaryName",
        "BoundaryType",
        "BoundaryMode",
        "BoundaryPlant",
        "BoundarySubplant",
        "BoundaryRegion",
        "BoundarySubRegion",
        "ReportArea",
        "LastUpdated"
      )
      SELECT
        R."Id"::uuid AS "ReportId",
        C."Id"::uuid AS "CustomerId",
        CASE
          WHEN RT."Description" = 'Compliance' THEN 'CR-' || SUBSTRING(R."Id"::text, 1, 6)
          WHEN RT."Description" = 'Emissions' THEN 'ER-' || SUBSTRING(R."Id"::text, 1, 6)
          ELSE 'CR-' || SUBSTRING(R."Id"::text, 1, 6)
        END AS "ReportName",
        R."DateStarted" AS "ReportDate",
        EXTRACT(YEAR FROM R."DateStarted")::int AS "ReportYear",
        EXTRACT(MONTH FROM R."DateStarted")::int AS "ReportMonth",
        EXTRACT(WEEK FROM R."DateStarted")::int AS "ReportWeek",
        RAC."AssetLengthKM" AS "ReportAssetLengthKm",
        RAC."AssetLengthKM" * RC."PercentCoverageAssets" AS "AssetCoveredLengthKm",
        RAC."DistributionPipeKm",
        RAC."DistributionPipeCoveredKm",
        RAC."ServicePipeKm",
        RAC."ServicePipeCoveredKm",
        dh.bo_name AS "BoundaryName",
        dh.bo_type AS "BoundaryType",
        dh.bo_mode AS "BoundaryMode",
        dh.bo_plant AS "BoundaryPlant",
        dh.bo_subplant AS "BoundarySubplant",
        dh.bo_region AS "BoundaryRegion",
        dh.bo_subregion AS "BoundarySubRegion",
        RA."Shape" AS "ReportArea",
        NOW() AS "LastUpdated"
      FROM %I."Report" R
      INNER JOIN %I."Customer" C ON R."CustomerId" = C."Id"
      LEFT JOIN %I."ReportLabel" RL ON R."Id" = RL."ReportId"
      LEFT JOIN %I."Label" L ON RL."LabelId" = L."Id"
      LEFT JOIN %I."ReportType" RT ON R."ReportTypeId" = RT."Id"
      LEFT JOIN %I."ReportCompliance" RC ON R."Id" = RC."ReportId"
      LEFT JOIN %I."ReportAreaCovered" RAC ON R."Id" = RAC."ReportId"
      LEFT JOIN %I."ReportArea" RA ON R."Id" = RA."ReportId"
      LEFT JOIN dash.v_report dh ON dh.rp_id = R."Id"::uuid
      WHERE C."Id"::uuid = $1
        AND L."Title" = 'Final Checkbox'
        AND RL."IsActive" = '1'
        AND R."DateStarted" >= $2
        AND R."DateStarted" < $3
        AND NOT EXISTS (
          SELECT 1
          FROM %s existing
          WHERE existing."ReportId" = R."Id"::uuid
        )
      ON CONFLICT ("ReportId") DO UPDATE SET
        "CustomerId" = EXCLUDED."CustomerId",
        "ReportName" = EXCLUDED."ReportName",
        "ReportDate" = EXCLUDED."ReportDate",
        "ReportYear" = EXCLUDED."ReportYear",
        "ReportMonth" = EXCLUDED."ReportMonth",
        "ReportWeek" = EXCLUDED."ReportWeek",
        "ReportAssetLengthKm" = EXCLUDED."ReportAssetLengthKm",
        "AssetCoveredLengthKm" = EXCLUDED."AssetCoveredLengthKm",
        "DistributionPipeKm" = EXCLUDED."DistributionPipeKm",
        "DistributionPipeCoveredKm" = EXCLUDED."DistributionPipeCoveredKm",
        "ServicePipeKm" = EXCLUDED."ServicePipeKm",
        "ServicePipeCoveredKm" = EXCLUDED."ServicePipeCoveredKm",
        "BoundaryName" = EXCLUDED."BoundaryName",
        "BoundaryType" = EXCLUDED."BoundaryType",
        "BoundaryMode" = EXCLUDED."BoundaryMode",
        "BoundaryPlant" = EXCLUDED."BoundaryPlant",
        "BoundarySubplant" = EXCLUDED."BoundarySubplant",
        "BoundaryRegion" = EXCLUDED."BoundaryRegion",
        "BoundarySubRegion" = EXCLUDED."BoundarySubRegion",
        "ReportArea" = EXCLUDED."ReportArea",
        "LastUpdated" = EXCLUDED."LastUpdated"
      $sql$,
      target_table,
      lsdb_schema, lsdb_schema, lsdb_schema, lsdb_schema, lsdb_schema,
      lsdb_schema, lsdb_schema, lsdb_schema, target_table
    ) USING p_customer_id, min_start_date, since_date;
  END IF;

  EXECUTE format(
    $sql$
    DELETE FROM %s existing
    WHERE existing."CustomerId" = $1
      AND existing."ReportDate" >= $2
      AND NOT EXISTS (
        SELECT 1
        FROM %I."Report" R
        INNER JOIN %I."ReportLabel" RL ON R."Id" = RL."ReportId"
        INNER JOIN %I."Label" L ON RL."LabelId" = L."Id"
        WHERE R."Id"::uuid = existing."ReportId"
          AND R."CustomerId"::uuid = existing."CustomerId"
          AND L."Title" = 'Final Checkbox'
          AND RL."IsActive" = '1'
          AND R."DateStarted" >= $2
      )
    $sql$,
    target_table,
    lsdb_schema,
    lsdb_schema,
    lsdb_schema
  ) USING p_customer_id, min_start_date;
END;
$$;

CREATE OR REPLACE PROCEDURE kpihub.refresh_report_summary_region(
  p_db_location text,
  p_since_date date DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
DECLARE
  rec record;
BEGIN
  FOR rec IN
    SELECT customerid, dblocation
    FROM kpihub."KPI_Customer"
    WHERE active IS TRUE
      AND upper(dblocation) = upper(p_db_location)
  LOOP
    CALL kpihub.refresh_report_summary_customer(rec.customerid, rec.dblocation, p_since_date);
  END LOOP;
END;
$$;

CREATE OR REPLACE PROCEDURE kpihub.refresh_report_summary()
LANGUAGE plpgsql
AS $$
DECLARE
  rec record;
BEGIN
  FOR rec IN
    SELECT customerid, dblocation
    FROM kpihub."KPI_Customer"
    WHERE active IS TRUE
  LOOP
    CALL kpihub.refresh_report_summary_customer(rec.customerid, rec.dblocation, NULL);
  END LOOP;
END;
$$;

CREATE VIEW kpihub."V_ReportSummary" AS
SELECT * FROM kpihub."MV_ReportSummary_eu1"
UNION ALL
SELECT * FROM kpihub."MV_ReportSummary_eu2";

COMMENT ON TABLE kpihub."MV_ReportSummary_eu1" IS
  'EU1 report summary snapshot. Refresh via CALL kpihub.refresh_report_summary_region(''EU1'').';

COMMENT ON TABLE kpihub."MV_ReportSummary_eu2" IS
  'EU2 report summary snapshot. Refresh via CALL kpihub.refresh_report_summary_region(''EU2'').';

COMMENT ON PROCEDURE kpihub.refresh_report_summary_customer(uuid, text, date) IS
  'Incremental sync of Final Checkbox reports from eu1/eu2 FDW into MV_ReportSummary tables.';

COMMENT ON PROCEDURE kpihub.refresh_report_summary() IS
  'Incremental sync for all active KPI_Customer rows.';
