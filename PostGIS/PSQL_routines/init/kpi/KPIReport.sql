-- KPIReport processor mirroring SQLite/lib/kpi_processor/KPIReport.py
--
-- Aggregates kpihub."V_ReportSummary" per customer and writes melted rows to
-- kpihub."KPI_Data" (same shape as KPISummary.melter / KPIReport.processor).
--
-- KPIs: FOVMain, ReportAssetLengthKm, AssetCoveredLengthKm, DistributionPipeKm,
--       DistributionPipeCoveredKm, ServicePipeKm, ServicePipeCoveredKm, ReportCount
--
-- Prerequisite:
--   1. IngesterTables.sql, SeedCustomerInfo.sql
--   2. ReportSummary.sql + REFRESH MATERIALIZED VIEW on MV_ReportSummary_eu1/eu2
--
-- Setup:
--   psql -U dsoler -d Datanalytics -v ON_ERROR_STOP=1 -f KPIReport.sql
--
-- Refresh:
--   CALL kpihub.refresh_kpi_report_customer('<customer-id>'::uuid);
--   CALL kpihub.refresh_kpi_report();

DO $$
BEGIN
  ALTER TABLE kpihub."KPI_Data"
    ALTER COLUMN periodtype TYPE TEXT USING periodtype::text;
EXCEPTION
  WHEN others THEN
    NULL;
END $$;

DROP FUNCTION IF EXISTS kpihub.kpi_report_build_id(text, text, integer, integer, text, text);

CREATE OR REPLACE FUNCTION kpihub.kpi_report_build_id(
  p_kpi_id text,
  p_customer_name text,
  p_report_year integer,
  p_report_week integer,
  p_boundary_region text,
  p_period_type text,
  p_include_boundary_region boolean DEFAULT false
)
RETURNS text
LANGUAGE sql
IMMUTABLE
AS $$
  SELECT
    p_kpi_id || '_' || p_customer_name
    || '_Y' || p_report_year::text
    || CASE
         WHEN p_include_boundary_region THEN
           '_B' || COALESCE(
             NULLIF(regexp_replace(p_boundary_region, '\s+', '', 'g'), ''),
             'NULL'
           )
         ELSE ''
       END
    || CASE
         WHEN p_period_type = 'Week' AND p_report_week IS NOT NULL
         THEN '_W' || p_report_week::text
         ELSE ''
       END;
$$;

CREATE OR REPLACE PROCEDURE kpihub.refresh_kpi_report_customer(
  p_customer_id uuid,
  p_include_boundary_region boolean DEFAULT false,
  p_period_type text DEFAULT 'Week'
)
LANGUAGE plpgsql
AS $$
DECLARE
  customer_name text;
  data_type text;
  kpi_ids text[] := ARRAY[
    'FOVMain',
    'ReportAssetLengthKm',
    'AssetCoveredLengthKm',
    'DistributionPipeKm',
    'DistributionPipeCoveredKm',
    'ServicePipeKm',
    'ServicePipeCoveredKm',
    'ReportCount'
  ];
BEGIN
  IF p_period_type NOT IN ('Week', 'Year') THEN
    RAISE EXCEPTION 'Unsupported period type: % (expected Week or Year)', p_period_type;
  END IF;

  SELECT "Name"
  INTO customer_name
  FROM kpihub."KPI_Customer"
  WHERE customerid = p_customer_id;

  IF customer_name IS NULL THEN
    RAISE EXCEPTION 'Customer % not found in KPI_Customer', p_customer_id;
  END IF;

  data_type := CASE
    WHEN p_include_boundary_region THEN 'KPIReportRegional'
    ELSE 'KPIReportGlobal'
  END;

  DELETE FROM kpihub."KPI_Data" kd
  WHERE kd.customerid = p_customer_id
    AND kd.kpiid = ANY(kpi_ids)
    AND kd.periodtype = p_period_type
    AND kd.datatype = data_type;

  IF p_period_type = 'Week' THEN
    INSERT INTO kpihub."KPI_Data" (
      id,
      kpiid,
      customerid,
      boundaryregion,
      "Year",
      periodtype,
      periodvalue,
      "Value",
      datatype,
      lastupdated
    )
    WITH aggregated AS (
      SELECT
        CASE
          WHEN p_include_boundary_region THEN r."BoundaryRegion"
          ELSE NULL::text
        END AS "BoundaryRegion",
        r."ReportYear",
        r."ReportWeek",
        ROUND(
          (100.0 * SUM(r."DistributionPipeCoveredKm")
            / NULLIF(SUM(r."DistributionPipeKm"), 0))::numeric,
          2
        ) AS "FOVMain",
        ROUND(SUM(r."ReportAssetLengthKm")::numeric, 2) AS "ReportAssetLengthKm",
        ROUND(SUM(r."AssetCoveredLengthKm")::numeric, 2) AS "AssetCoveredLengthKm",
        ROUND(SUM(r."DistributionPipeKm")::numeric, 2) AS "DistributionPipeKm",
        ROUND(SUM(r."DistributionPipeCoveredKm")::numeric, 2) AS "DistributionPipeCoveredKm",
        ROUND(SUM(r."ServicePipeKm")::numeric, 2) AS "ServicePipeKm",
        ROUND(SUM(r."ServicePipeCoveredKm")::numeric, 2) AS "ServicePipeCoveredKm",
        COUNT(*)::integer AS "ReportCount"
      FROM kpihub."V_ReportSummary" r
      WHERE r."CustomerId" = p_customer_id
      GROUP BY
        CASE
          WHEN p_include_boundary_region THEN r."BoundaryRegion"
          ELSE NULL::text
        END,
        r."ReportYear",
        r."ReportWeek"
    ),
    melted AS (
      SELECT
        a."BoundaryRegion",
        a."ReportYear",
        a."ReportWeek",
        m.kpi_id,
        m.kpi_value
      FROM aggregated a
      CROSS JOIN LATERAL (
        VALUES
          ('FOVMain', a."FOVMain"::text),
          ('ReportAssetLengthKm', a."ReportAssetLengthKm"::text),
          ('AssetCoveredLengthKm', a."AssetCoveredLengthKm"::text),
          ('DistributionPipeKm', a."DistributionPipeKm"::text),
          ('DistributionPipeCoveredKm', a."DistributionPipeCoveredKm"::text),
          ('ServicePipeKm', a."ServicePipeKm"::text),
          ('ServicePipeCoveredKm', a."ServicePipeCoveredKm"::text),
          ('ReportCount', a."ReportCount"::text)
      ) AS m(kpi_id, kpi_value)
      WHERE m.kpi_value IS NOT NULL
    )
    SELECT
      kpihub.kpi_report_build_id(
        m.kpi_id,
        customer_name,
        m."ReportYear",
        m."ReportWeek",
        m."BoundaryRegion",
        p_period_type,
        p_include_boundary_region
      ),
      m.kpi_id,
      p_customer_id,
      m."BoundaryRegion",
      m."ReportYear",
      p_period_type,
      m."ReportWeek",
      m.kpi_value,
      data_type,
      NOW()
    FROM melted m;
  ELSE
    INSERT INTO kpihub."KPI_Data" (
      id,
      kpiid,
      customerid,
      boundaryregion,
      "Year",
      periodtype,
      periodvalue,
      "Value",
      datatype,
      lastupdated
    )
    WITH aggregated AS (
      SELECT
        CASE
          WHEN p_include_boundary_region THEN r."BoundaryRegion"
          ELSE NULL::text
        END AS "BoundaryRegion",
        r."ReportYear",
        ROUND(
          (100.0 * SUM(r."DistributionPipeCoveredKm")
            / NULLIF(SUM(r."DistributionPipeKm"), 0))::numeric,
          2
        ) AS "FOVMain",
        ROUND(SUM(r."ReportAssetLengthKm")::numeric, 2) AS "ReportAssetLengthKm",
        ROUND(SUM(r."AssetCoveredLengthKm")::numeric, 2) AS "AssetCoveredLengthKm",
        ROUND(SUM(r."DistributionPipeKm")::numeric, 2) AS "DistributionPipeKm",
        ROUND(SUM(r."DistributionPipeCoveredKm")::numeric, 2) AS "DistributionPipeCoveredKm",
        ROUND(SUM(r."ServicePipeKm")::numeric, 2) AS "ServicePipeKm",
        ROUND(SUM(r."ServicePipeCoveredKm")::numeric, 2) AS "ServicePipeCoveredKm",
        COUNT(*)::integer AS "ReportCount"
      FROM kpihub."V_ReportSummary" r
      WHERE r."CustomerId" = p_customer_id
      GROUP BY
        CASE
          WHEN p_include_boundary_region THEN r."BoundaryRegion"
          ELSE NULL::text
        END,
        r."ReportYear"
    ),
    melted AS (
      SELECT
        a."BoundaryRegion",
        a."ReportYear",
        m.kpi_id,
        m.kpi_value
      FROM aggregated a
      CROSS JOIN LATERAL (
        VALUES
          ('FOVMain', a."FOVMain"::text),
          ('ReportAssetLengthKm', a."ReportAssetLengthKm"::text),
          ('AssetCoveredLengthKm', a."AssetCoveredLengthKm"::text),
          ('DistributionPipeKm', a."DistributionPipeKm"::text),
          ('DistributionPipeCoveredKm', a."DistributionPipeCoveredKm"::text),
          ('ServicePipeKm', a."ServicePipeKm"::text),
          ('ServicePipeCoveredKm', a."ServicePipeCoveredKm"::text),
          ('ReportCount', a."ReportCount"::text)
      ) AS m(kpi_id, kpi_value)
      WHERE m.kpi_value IS NOT NULL
    )
    SELECT
      kpihub.kpi_report_build_id(
        m.kpi_id,
        customer_name,
        m."ReportYear",
        NULL,
        m."BoundaryRegion",
        p_period_type,
        p_include_boundary_region
      ),
      m.kpi_id,
      p_customer_id,
      m."BoundaryRegion",
      m."ReportYear",
      p_period_type,
      NULL,
      m.kpi_value,
      data_type,
      NOW()
    FROM melted m;
  END IF;
END;
$$;

CREATE OR REPLACE PROCEDURE kpihub.refresh_kpi_report_customer_all(
  p_customer_id uuid
)
LANGUAGE plpgsql
AS $$
BEGIN
  -- Mirrors SQLite/processes/KPIProcessing.py KPIReport invocations
  CALL kpihub.refresh_kpi_report_customer(p_customer_id, false, 'Week');
  CALL kpihub.refresh_kpi_report_customer(p_customer_id, true, 'Week');
  CALL kpihub.refresh_kpi_report_customer(p_customer_id, false, 'Year');
  CALL kpihub.refresh_kpi_report_customer(p_customer_id, true, 'Year');
END;
$$;

CREATE OR REPLACE PROCEDURE kpihub.refresh_kpi_report()
LANGUAGE plpgsql
AS $$
DECLARE
  cust record;
BEGIN
  FOR cust IN
    SELECT customerid
    FROM kpihub."KPI_Customer"
    WHERE active IS TRUE
    ORDER BY "Name"
  LOOP
    CALL kpihub.refresh_kpi_report_customer_all(cust.customerid);
  END LOOP;
END;
$$;

COMMENT ON FUNCTION kpihub.kpi_report_build_id IS
  'Build KPI_Data.Id using the same pattern as KPISummary.generate_id in KPIReport.py.';

COMMENT ON PROCEDURE kpihub.refresh_kpi_report_customer(uuid, boolean, text) IS
  'Compute KPIReport metrics from V_ReportSummary and upsert into KPI_Data.';

COMMENT ON PROCEDURE kpihub.refresh_kpi_report() IS
  'Refresh KPIReport KPIs (weekly/yearly, global/regional) for all active customers.';
