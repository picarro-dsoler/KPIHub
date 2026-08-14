-- Report summary materialized views mirroring lib/ingester/ReportSummaryIngester.py
-- Sources: eu1/eu2 foreign tables (LSDB) + dash.v_report (DataHub)
--
-- Only reports for customers in kpihub."KPI_Customer" with active = true are loaded.
-- Refresh builds each MV from a session temp table of active customers.
-- ReportArea is stored in companion cache tables and loaded separately via
-- refresh_report_areas() to avoid pulling all Shape blobs through tds_fdw at once.
--
-- Prerequisite:
--   1. psql ... -f IngesterTables.sql
--   2. psql ... -f SeedCustomerInfo.sql
--      or: python3 PostGIS/init/SeedCustomerInfo.py
--
-- Setup:
--   psql -U dsoler -d Datanalytics -v ON_ERROR_STOP=1 -f ReportSummaryMaterializedView.sql
--
-- Load / refresh data:
--   CALL kpihub.refresh_report_summary();
--   CALL kpihub.refresh_report_areas();          -- optional, for survey intersection

SET enable_mergejoin = off;
SET work_mem = '256MB';
SET maintenance_work_mem = '512MB';

DROP VIEW IF EXISTS kpihub."V_ReportSummary";
DROP VIEW IF EXISTS kpihub."V_ReportSummary_WithArea";

DROP MATERIALIZED VIEW IF EXISTS kpihub."MV_ReportSummary_eu1";
DROP MATERIALIZED VIEW IF EXISTS kpihub."MV_ReportSummary_eu2";
DROP MATERIALIZED VIEW IF EXISTS kpihub."MV_ReportSummary";

DROP TABLE IF EXISTS kpihub."MV_ReportSummary_eu1";
DROP TABLE IF EXISTS kpihub."MV_ReportSummary_eu2";

DROP TABLE IF EXISTS kpihub."ReportAreaCache_eu1";
DROP TABLE IF EXISTS kpihub."ReportAreaCache_eu2";

CREATE MATERIALIZED VIEW kpihub."MV_ReportSummary_eu1" AS
SELECT
  R."Id" AS "ReportId",
  C."Id" AS "CustomerId",
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
  NULL::geometry AS "ReportArea",
  NOW() AS "LastUpdated"
FROM eu1."Report" R
INNER JOIN eu1."Customer" C ON R."CustomerId" = C."Id"
INNER JOIN kpihub."KPI_Customer" kc
  ON kc.customerid = C."Id"
 AND kc.active IS TRUE
 AND kc.dblocation IS NOT NULL
 AND upper(kc.dblocation) = 'EU1'
LEFT JOIN eu1."ReportLabel" RL ON R."Id" = RL."ReportId"
LEFT JOIN eu1."Label" L ON RL."LabelId" = L."Id"
LEFT JOIN eu1."ReportType" RT ON R."ReportTypeId" = RT."Id"
LEFT JOIN eu1."ReportCompliance" RC ON R."Id" = RC."ReportId"
LEFT JOIN eu1."ReportAreaCovered" RAC ON R."Id" = RAC."ReportId"
LEFT JOIN dash.v_report dh ON dh.rp_id = R."Id"
WHERE L."Title" = 'Final Checkbox'
  AND RL."IsActive" = 1
  AND R."DateStarted" >= DATE '2023-01-01'
WITH NO DATA;

CREATE MATERIALIZED VIEW kpihub."MV_ReportSummary_eu2" AS
SELECT
  R."Id" AS "ReportId",
  C."Id" AS "CustomerId",
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
  NULL::geometry AS "ReportArea",
  NOW() AS "LastUpdated"
FROM eu2."Report" R
INNER JOIN eu2."Customer" C ON R."CustomerId" = C."Id"
INNER JOIN kpihub."KPI_Customer" kc
  ON kc.customerid = C."Id"
 AND kc.active IS TRUE
 AND kc.dblocation IS NOT NULL
 AND upper(kc.dblocation) = 'EU2'
LEFT JOIN eu2."ReportLabel" RL ON R."Id" = RL."ReportId"
LEFT JOIN eu2."Label" L ON RL."LabelId" = L."Id"
LEFT JOIN eu2."ReportType" RT ON R."ReportTypeId" = RT."Id"
LEFT JOIN eu2."ReportCompliance" RC ON R."Id" = RC."ReportId"
LEFT JOIN eu2."ReportAreaCovered" RAC ON R."Id" = RAC."ReportId"
LEFT JOIN dash.v_report dh ON dh.rp_id = R."Id"
WHERE L."Title" = 'Final Checkbox'
  AND RL."IsActive" = 1
  AND R."DateStarted" >= DATE '2023-01-01'
WITH NO DATA;

CREATE UNIQUE INDEX "MV_ReportSummary_eu1_ReportId_idx"
  ON kpihub."MV_ReportSummary_eu1" ("ReportId");

CREATE UNIQUE INDEX "MV_ReportSummary_eu2_ReportId_idx"
  ON kpihub."MV_ReportSummary_eu2" ("ReportId");

CREATE INDEX "MV_ReportSummary_eu1_CustomerId_idx"
  ON kpihub."MV_ReportSummary_eu1" ("CustomerId");

CREATE INDEX "MV_ReportSummary_eu2_CustomerId_idx"
  ON kpihub."MV_ReportSummary_eu2" ("CustomerId");

CREATE INDEX "MV_ReportSummary_eu1_ReportDate_idx"
  ON kpihub."MV_ReportSummary_eu1" ("ReportDate");

CREATE INDEX "MV_ReportSummary_eu2_ReportDate_idx"
  ON kpihub."MV_ReportSummary_eu2" ("ReportDate");

CREATE TABLE kpihub."ReportAreaCache_eu1" (
  "ReportId" uuid PRIMARY KEY,
  "ReportArea" geometry
);

CREATE TABLE kpihub."ReportAreaCache_eu2" (
  LIKE kpihub."ReportAreaCache_eu1" INCLUDING ALL
);

CREATE OR REPLACE PROCEDURE kpihub._ensure_report_summary_mv_indexes(
  p_db_location text
)
LANGUAGE plpgsql
AS $$
DECLARE
  mv_name text;
  suffix text;
BEGIN
  IF upper(p_db_location) = 'EU2' THEN
    mv_name := 'kpihub."MV_ReportSummary_eu2"';
    suffix := 'eu2';
  ELSIF upper(p_db_location) = 'EU1' THEN
    mv_name := 'kpihub."MV_ReportSummary_eu1"';
    suffix := 'eu1';
  ELSE
    RAISE EXCEPTION 'Unsupported DB location: % (expected EU1 or EU2)', p_db_location;
  END IF;

  EXECUTE format(
    'CREATE UNIQUE INDEX IF NOT EXISTS %I ON %s ("ReportId")',
    'MV_ReportSummary_' || suffix || '_ReportId_idx',
    mv_name
  );
  EXECUTE format(
    'CREATE INDEX IF NOT EXISTS %I ON %s ("CustomerId")',
    'MV_ReportSummary_' || suffix || '_CustomerId_idx',
    mv_name
  );
  EXECUTE format(
    'CREATE INDEX IF NOT EXISTS %I ON %s ("ReportDate")',
    'MV_ReportSummary_' || suffix || '_ReportDate_idx',
    mv_name
  );
END;
$$;

CREATE OR REPLACE PROCEDURE kpihub._rebuild_report_summary_mv(
  p_db_location text,
  p_source_query text DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
DECLARE
  lsdb_schema text;
  mv_name text;
  db_location_label text;
BEGIN
  IF upper(p_db_location) = 'EU2' THEN
    lsdb_schema := 'eu2';
    mv_name := 'kpihub."MV_ReportSummary_eu2"';
    db_location_label := 'EU2';
  ELSIF upper(p_db_location) = 'EU1' THEN
    lsdb_schema := 'eu1';
    mv_name := 'kpihub."MV_ReportSummary_eu1"';
    db_location_label := 'EU1';
  ELSE
    RAISE EXCEPTION 'Unsupported DB location: % (expected EU1 or EU2)', p_db_location;
  END IF;

  EXECUTE format('DROP MATERIALIZED VIEW IF EXISTS %s', mv_name);

  IF p_source_query IS NULL THEN
    EXECUTE format(
      $sql$
      CREATE MATERIALIZED VIEW %s AS
      SELECT
        R."Id" AS "ReportId",
        C."Id" AS "CustomerId",
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
        NULL::geometry AS "ReportArea",
        NOW() AS "LastUpdated"
      FROM %I."Report" R
      INNER JOIN %I."Customer" C ON R."CustomerId" = C."Id"
      INNER JOIN tmp_active_customers ac
        ON ac.customerid = C."Id"
       AND upper(ac.dblocation) = %L
      LEFT JOIN %I."ReportLabel" RL ON R."Id" = RL."ReportId"
      LEFT JOIN %I."Label" L ON RL."LabelId" = L."Id"
      LEFT JOIN %I."ReportType" RT ON R."ReportTypeId" = RT."Id"
      LEFT JOIN %I."ReportCompliance" RC ON R."Id" = RC."ReportId"
      LEFT JOIN %I."ReportAreaCovered" RAC ON R."Id" = RAC."ReportId"
      LEFT JOIN dash.v_report dh ON dh.rp_id = R."Id"
      WHERE L."Title" = 'Final Checkbox'
        AND RL."IsActive" = 1
        AND R."DateStarted" >= DATE '2023-01-01'
      WITH DATA
      $sql$,
      mv_name,
      lsdb_schema,
      lsdb_schema,
      db_location_label,
      lsdb_schema,
      lsdb_schema,
      lsdb_schema,
      lsdb_schema,
      lsdb_schema
    );
  ELSE
    EXECUTE format(
      'CREATE MATERIALIZED VIEW %s AS %s WITH DATA',
      mv_name,
      p_source_query
    );
  END IF;

  CALL kpihub._ensure_report_summary_mv_indexes(p_db_location);
END;
$$;

CREATE OR REPLACE PROCEDURE kpihub.refresh_report_summary_customer(
  p_customer_id uuid,
  p_db_location text
)
LANGUAGE plpgsql
AS $$
DECLARE
  lsdb_schema text;
  mv_name text;
  cache_table text;
  active_count integer;
BEGIN
  IF upper(p_db_location) = 'EU2' THEN
    lsdb_schema := 'eu2';
    mv_name := 'kpihub."MV_ReportSummary_eu2"';
    cache_table := 'kpihub."ReportAreaCache_eu2"';
  ELSIF upper(p_db_location) = 'EU1' THEN
    lsdb_schema := 'eu1';
    mv_name := 'kpihub."MV_ReportSummary_eu1"';
    cache_table := 'kpihub."ReportAreaCache_eu1"';
  ELSE
    RAISE EXCEPTION 'Unsupported DB location: % (expected EU1 or EU2)', p_db_location;
  END IF;

  DROP TABLE IF EXISTS tmp_active_customers;
  CREATE TEMP TABLE tmp_active_customers ON COMMIT DROP AS
  SELECT customerid, dblocation, "Name"
  FROM kpihub."KPI_Customer"
  WHERE active IS TRUE
    AND customerid = p_customer_id
    AND dblocation IS NOT NULL
    AND upper(dblocation) = upper(p_db_location);

  GET DIAGNOSTICS active_count = ROW_COUNT;
  IF active_count = 0 THEN
    RAISE EXCEPTION
      'Customer % is not an active % customer in kpihub.KPI_Customer',
      p_customer_id,
      upper(p_db_location);
  END IF;

  DROP TABLE IF EXISTS tmp_customer_rows;
  EXECUTE format(
    $sql$
    CREATE TEMP TABLE tmp_customer_rows ON COMMIT DROP AS
    SELECT
      R."Id" AS "ReportId",
      C."Id" AS "CustomerId",
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
      NULL::geometry AS "ReportArea",
      NOW() AS "LastUpdated"
    FROM %I."Report" R
    INNER JOIN %I."Customer" C ON R."CustomerId" = C."Id"
    INNER JOIN tmp_active_customers ac ON ac.customerid = C."Id"
    LEFT JOIN %I."ReportLabel" RL ON R."Id" = RL."ReportId"
    LEFT JOIN %I."Label" L ON RL."LabelId" = L."Id"
    LEFT JOIN %I."ReportType" RT ON R."ReportTypeId" = RT."Id"
    LEFT JOIN %I."ReportCompliance" RC ON R."Id" = RC."ReportId"
    LEFT JOIN %I."ReportAreaCovered" RAC ON R."Id" = RAC."ReportId"
    LEFT JOIN dash.v_report dh ON dh.rp_id = R."Id"
    WHERE L."Title" = 'Final Checkbox'
      AND RL."IsActive" = 1
      AND R."DateStarted" >= DATE '2023-01-01'
    $sql$,
    lsdb_schema,
    lsdb_schema,
    lsdb_schema,
    lsdb_schema,
    lsdb_schema,
    lsdb_schema,
    lsdb_schema
  );

  DROP TABLE IF EXISTS tmp_old_report_ids;
  EXECUTE format(
    $sql$
    CREATE TEMP TABLE tmp_old_report_ids ON COMMIT DROP AS
    SELECT "ReportId"
    FROM %s
    WHERE "CustomerId" = $1
    $sql$,
    mv_name
  ) USING p_customer_id;

  DROP TABLE IF EXISTS tmp_merged_rows;
  EXECUTE format(
    $sql$
    CREATE TEMP TABLE tmp_merged_rows ON COMMIT DROP AS
    SELECT *
    FROM %s
    WHERE "CustomerId" <> $1
    UNION ALL
    SELECT * FROM tmp_customer_rows
    $sql$,
    mv_name
  ) USING p_customer_id;

  CALL kpihub._rebuild_report_summary_mv(
    p_db_location,
    'SELECT * FROM tmp_merged_rows'
  );

  EXECUTE format(
    $sql$
    DELETE FROM %s
    WHERE "ReportId" IN (
      SELECT old_rows."ReportId"
      FROM tmp_old_report_ids old_rows
      EXCEPT
      SELECT new_rows."ReportId"
      FROM tmp_customer_rows new_rows
    )
    $sql$,
    cache_table
  );
END;
$$;

CREATE OR REPLACE PROCEDURE kpihub.refresh_report_area_report(
  p_report_id uuid,
  p_db_location text
)
LANGUAGE plpgsql
AS $$
DECLARE
  lsdb_schema text;
  cache_table text;
BEGIN
  IF upper(p_db_location) = 'EU2' THEN
    lsdb_schema := 'eu2';
    cache_table := 'kpihub."ReportAreaCache_eu2"';
  ELSIF upper(p_db_location) = 'EU1' THEN
    lsdb_schema := 'eu1';
    cache_table := 'kpihub."ReportAreaCache_eu1"';
  ELSE
    RAISE EXCEPTION 'Unsupported DB location: % (expected EU1 or EU2)', p_db_location;
  END IF;

  EXECUTE format(
    $sql$
    INSERT INTO %s ("ReportId", "ReportArea")
    SELECT
      RA."ReportId",
      ST_GeomFromText(RA."Shape", 4326)
    FROM %I."ReportArea" RA
    WHERE RA."ReportId" = $1
      AND RA."Shape" IS NOT NULL
      AND btrim(RA."Shape") <> ''
    ON CONFLICT ("ReportId") DO UPDATE
      SET "ReportArea" = EXCLUDED."ReportArea"
    $sql$,
    cache_table,
    lsdb_schema
  ) USING p_report_id;
END;
$$;

CREATE OR REPLACE PROCEDURE kpihub.refresh_report_areas_customer(
  p_customer_id uuid,
  p_db_location text
)
LANGUAGE plpgsql
AS $$
DECLARE
  mv_name text;
  rep record;
BEGIN
  IF upper(p_db_location) = 'EU2' THEN
    mv_name := 'kpihub."MV_ReportSummary_eu2"';
  ELSIF upper(p_db_location) = 'EU1' THEN
    mv_name := 'kpihub."MV_ReportSummary_eu1"';
  ELSE
    RAISE EXCEPTION 'Unsupported DB location: % (expected EU1 or EU2)', p_db_location;
  END IF;

  FOR rep IN
    EXECUTE format(
      'SELECT "ReportId" FROM %s WHERE "CustomerId" = $1 ORDER BY "ReportDate"',
      mv_name
    )
    USING p_customer_id
  LOOP
    CALL kpihub.refresh_report_area_report(rep."ReportId", p_db_location);
  END LOOP;
END;
$$;

CREATE OR REPLACE PROCEDURE kpihub.refresh_report_areas()
LANGUAGE plpgsql
AS $$
DECLARE
  cust record;
BEGIN
  SET LOCAL enable_mergejoin = off;

  DROP TABLE IF EXISTS tmp_active_customers;
  CREATE TEMP TABLE tmp_active_customers ON COMMIT DROP AS
  SELECT customerid, dblocation, "Name"
  FROM kpihub."KPI_Customer"
  WHERE active IS TRUE
    AND dblocation IS NOT NULL
    AND upper(dblocation) IN ('EU1', 'EU2');

  FOR cust IN
    SELECT customerid, dblocation
    FROM tmp_active_customers
    ORDER BY "Name"
  LOOP
    CALL kpihub.refresh_report_areas_customer(cust.customerid, cust.dblocation);
  END LOOP;
END;
$$;

CREATE OR REPLACE PROCEDURE kpihub.refresh_report_summary()
LANGUAGE plpgsql
AS $$
BEGIN
  SET LOCAL enable_mergejoin = off;

  DROP TABLE IF EXISTS tmp_active_customers;
  CREATE TEMP TABLE tmp_active_customers ON COMMIT DROP AS
  SELECT customerid, dblocation, "Name"
  FROM kpihub."KPI_Customer"
  WHERE active IS TRUE
    AND dblocation IS NOT NULL
    AND upper(dblocation) IN ('EU1', 'EU2');

  TRUNCATE TABLE kpihub."ReportAreaCache_eu1";
  TRUNCATE TABLE kpihub."ReportAreaCache_eu2";

  CALL kpihub._rebuild_report_summary_mv('EU1');
  CALL kpihub._rebuild_report_summary_mv('EU2');
END;
$$;

CREATE VIEW kpihub."V_ReportSummary" AS
SELECT
  m."ReportId",
  m."CustomerId",
  m."ReportName",
  m."ReportDate",
  m."ReportYear",
  m."ReportMonth",
  m."ReportWeek",
  m."ReportAssetLengthKm",
  m."AssetCoveredLengthKm",
  m."DistributionPipeKm",
  m."DistributionPipeCoveredKm",
  m."ServicePipeKm",
  m."ServicePipeCoveredKm",
  m."BoundaryName",
  m."BoundaryType",
  m."BoundaryMode",
  m."BoundaryPlant",
  m."BoundarySubplant",
  m."BoundaryRegion",
  m."BoundarySubRegion",
  COALESCE(ra."ReportArea", m."ReportArea") AS "ReportArea",
  m."LastUpdated"
FROM kpihub."MV_ReportSummary_eu1" m
LEFT JOIN kpihub."ReportAreaCache_eu1" ra ON ra."ReportId" = m."ReportId"
UNION ALL
SELECT
  m."ReportId",
  m."CustomerId",
  m."ReportName",
  m."ReportDate",
  m."ReportYear",
  m."ReportMonth",
  m."ReportWeek",
  m."ReportAssetLengthKm",
  m."AssetCoveredLengthKm",
  m."DistributionPipeKm",
  m."DistributionPipeCoveredKm",
  m."ServicePipeKm",
  m."ServicePipeCoveredKm",
  m."BoundaryName",
  m."BoundaryType",
  m."BoundaryMode",
  m."BoundaryPlant",
  m."BoundarySubplant",
  m."BoundaryRegion",
  m."BoundarySubRegion",
  COALESCE(ra."ReportArea", m."ReportArea") AS "ReportArea",
  m."LastUpdated"
FROM kpihub."MV_ReportSummary_eu2" m
LEFT JOIN kpihub."ReportAreaCache_eu2" ra ON ra."ReportId" = m."ReportId";

COMMENT ON MATERIALIZED VIEW kpihub."MV_ReportSummary_eu1" IS
  'EU1 report summary snapshot for active KPI_Customer rows. Refresh via CALL kpihub.refresh_report_summary().';

COMMENT ON MATERIALIZED VIEW kpihub."MV_ReportSummary_eu2" IS
  'EU2 report summary snapshot for active KPI_Customer rows. Refresh via CALL kpihub.refresh_report_summary().';

COMMENT ON PROCEDURE kpihub.refresh_report_summary() IS
  'Rebuild report summary materialized views from active customers in kpihub.KPI_Customer.';

-- Next: EmissionSourceSummaryMaterializedView.sql
