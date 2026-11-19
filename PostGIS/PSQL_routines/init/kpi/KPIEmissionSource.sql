-- KPIEmissionSource processor mirroring SQLite/lib/kpi_processor/KPIReport.py
--
-- Joins kpihub."V_ReportSummary" with kpihub."V_EmissionSourceSummary", aggregates
-- per customer, and writes melted rows to kpihub."KPI_Data".
--
-- Prerequisite:
--   1. IngesterTables.sql, SeedCustomerInfo.sql
--   2. ReportSummary.sql + EmissionSourceSummaryMaterializedView.sql refreshed
--   3. KPIReport.sql (reuses kpihub.kpi_report_build_id)
--
-- Setup:
--   psql -U dsoler -d Datanalytics -v ON_ERROR_STOP=1 -f KPIEmissionSource.sql
--
-- Refresh:
--   CALL kpihub.refresh_kpi_emission_source_customer('<customer-id>'::uuid);
--   CALL kpihub.refresh_kpi_emission_source();

CREATE OR REPLACE PROCEDURE kpihub.refresh_kpi_emission_source_customer(
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
    'LisaCount', 'EmissionRate', 'B0Count', 'B1Count', 'Bm1Count', 'Bm2Count',
    'NGCount', 'PGCount', 'Not_NGCount', 'EmissionRateLPM', 'RepresentativeEmissionRate',
    'RepresentativeEmissionRateLPM', 'B0RepEmissionRateLPM', 'B1RepEmissionRateLPM',
    'Bm1RepEmissionRateLPM', 'Bm2RepEmissionRateLPM', 'B0RepEmissionRate', 'B1RepEmissionRate',
    'Bm1RepEmissionRate', 'Bm2RepEmissionRate', 'LisaDensity', 'InstatanoeusEmission',
    'InstatanoeusEmissionLPM', 'InstatanoeusRepEmission', 'InstatanoeusRepEmissionLPM',
    'B0Density', 'B1Density', 'Bm1Density', 'Bm2Density', 'NGDensity', 'PGDensity',
    'B0Share', 'B1Share', 'Bm1Share', 'Bm2Share', 'NGShare', 'PGShare', 'Not_NGShare'
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
    WHEN p_include_boundary_region THEN 'KPIEmissionSourceRegional'
    ELSE 'KPIEmissionSourceGlobal'
  END;

  DELETE FROM kpihub."KPI_Data" kd
  WHERE kd.customerid = p_customer_id
    AND kd.kpiid = ANY(kpi_ids)
    AND kd.periodtype = p_period_type
    AND kd.datatype = data_type;

  IF p_period_type = 'Week' THEN
    INSERT INTO kpihub."KPI_Data" (
      id, kpiid, customerid, boundaryregion, "Year", periodtype, periodvalue,
      "Value", datatype, lastupdated
    )
    WITH base AS (
      SELECT
        CASE
          WHEN p_include_boundary_region THEN r."BoundaryRegion"
          ELSE NULL::text
        END AS "BoundaryRegion",
        r."ReportYear",
        r."ReportWeek",
        r."DistributionPipeCoveredKm",
        e."LisaCount",
        e."EmissionRate",
        e."B0Count",
        e."B1Count",
        e."Bm1Count",
        e."Bm2Count",
        e."NGCount",
        e."PGCount",
        e."Not_NGCount",
        e."EmissionRateLPM",
        e."RepresentativeEmissionRate",
        e."RepresentativeEmissionRateLPM",
        e."B0RepEmissionRateLPM",
        e."B1RepEmissionRateLPM",
        e."Bm1RepEmissionRateLPM",
        e."Bm2RepEmissionRateLPM",
        e."B0RepEmissionRate",
        e."B1RepEmissionRate",
        e."Bm1RepEmissionRate",
        e."Bm2RepEmissionRate"
      FROM kpihub."V_ReportSummary" r
      INNER JOIN kpihub."V_EmissionSourceSummary" e ON e."ReportId" = r."ReportId"
      WHERE r."CustomerId" = p_customer_id
    ),
    aggregated AS (
      SELECT
        "BoundaryRegion",
        "ReportYear",
        "ReportWeek",
        SUM("DistributionPipeCoveredKm") AS denom,
        ROUND(SUM("LisaCount")::numeric, 2) AS "LisaCount",
        ROUND(SUM("EmissionRate")::numeric, 2) AS "EmissionRate",
        ROUND(SUM("B0Count")::numeric, 2) AS "B0Count",
        ROUND(SUM("B1Count")::numeric, 2) AS "B1Count",
        ROUND(SUM("Bm1Count")::numeric, 2) AS "Bm1Count",
        ROUND(SUM("Bm2Count")::numeric, 2) AS "Bm2Count",
        ROUND(SUM("NGCount")::numeric, 2) AS "NGCount",
        ROUND(SUM("PGCount")::numeric, 2) AS "PGCount",
        ROUND(SUM("Not_NGCount")::numeric, 2) AS "Not_NGCount",
        ROUND(SUM("EmissionRateLPM")::numeric, 2) AS "EmissionRateLPM",
        ROUND(SUM("RepresentativeEmissionRate")::numeric, 2) AS "RepresentativeEmissionRate",
        ROUND(SUM("RepresentativeEmissionRateLPM")::numeric, 2) AS "RepresentativeEmissionRateLPM",
        ROUND(SUM("B0RepEmissionRateLPM")::numeric, 2) AS "B0RepEmissionRateLPM",
        ROUND(SUM("B1RepEmissionRateLPM")::numeric, 2) AS "B1RepEmissionRateLPM",
        ROUND(SUM("Bm1RepEmissionRateLPM")::numeric, 2) AS "Bm1RepEmissionRateLPM",
        ROUND(SUM("Bm2RepEmissionRateLPM")::numeric, 2) AS "Bm2RepEmissionRateLPM",
        ROUND(SUM("B0RepEmissionRate")::numeric, 2) AS "B0RepEmissionRate",
        ROUND(SUM("B1RepEmissionRate")::numeric, 2) AS "B1RepEmissionRate",
        ROUND(SUM("Bm1RepEmissionRate")::numeric, 2) AS "Bm1RepEmissionRate",
        ROUND(SUM("Bm2RepEmissionRate")::numeric, 2) AS "Bm2RepEmissionRate"
      FROM base
      GROUP BY "BoundaryRegion", "ReportYear", "ReportWeek"
    ),
    metrics AS (
      SELECT
        a.*,
        CASE WHEN denom > 0 THEN ROUND(("LisaCount" / denom)::numeric, 2) END AS "LisaDensity",
        CASE WHEN denom > 0 THEN ROUND(("EmissionRate" / denom)::numeric, 2) END AS "InstatanoeusEmission",
        CASE WHEN denom > 0 THEN ROUND(("EmissionRateLPM" / denom)::numeric, 2) END AS "InstatanoeusEmissionLPM",
        CASE WHEN denom > 0 THEN ROUND(("RepresentativeEmissionRate" / denom)::numeric, 2) END AS "InstatanoeusRepEmission",
        CASE WHEN denom > 0 THEN ROUND(("RepresentativeEmissionRateLPM" / denom)::numeric, 2) END AS "InstatanoeusRepEmissionLPM",
        CASE WHEN denom > 0 THEN ROUND(("B0Count" / denom)::numeric, 2) END AS "B0Density",
        CASE WHEN denom > 0 THEN ROUND(("B1Count" / denom)::numeric, 2) END AS "B1Density",
        CASE WHEN denom > 0 THEN ROUND(("Bm1Count" / denom)::numeric, 2) END AS "Bm1Density",
        CASE WHEN denom > 0 THEN ROUND(("Bm2Count" / denom)::numeric, 2) END AS "Bm2Density",
        CASE WHEN denom > 0 THEN ROUND(("NGCount" / denom)::numeric, 2) END AS "NGDensity",
        CASE WHEN denom > 0 THEN ROUND(("PGCount" / denom)::numeric, 2) END AS "PGDensity",
        CASE WHEN "LisaCount" > 0 THEN ROUND((100.0 * "B0Count" / "LisaCount")::numeric, 2) END AS "B0Share",
        CASE WHEN "LisaCount" > 0 THEN ROUND((100.0 * "B1Count" / "LisaCount")::numeric, 2) END AS "B1Share",
        CASE WHEN "LisaCount" > 0 THEN ROUND((100.0 * "Bm1Count" / "LisaCount")::numeric, 2) END AS "Bm1Share",
        CASE WHEN "LisaCount" > 0 THEN ROUND((100.0 * "Bm2Count" / "LisaCount")::numeric, 2) END AS "Bm2Share",
        CASE WHEN ("NGCount" + "Not_NGCount" + "PGCount") > 0
          THEN ROUND((100.0 * "NGCount" / ("NGCount" + "Not_NGCount" + "PGCount"))::numeric, 2)
        END AS "NGShare",
        CASE WHEN ("NGCount" + "Not_NGCount" + "PGCount") > 0
          THEN ROUND((100.0 * "PGCount" / ("NGCount" + "Not_NGCount" + "PGCount"))::numeric, 2)
        END AS "PGShare",
        CASE WHEN ("NGCount" + "Not_NGCount" + "PGCount") > 0
          THEN ROUND((100.0 * "Not_NGCount" / ("NGCount" + "Not_NGCount" + "PGCount"))::numeric, 2)
        END AS "Not_NGShare"
      FROM aggregated a
    ),
    melted AS (
      SELECT m."BoundaryRegion", m."ReportYear", m."ReportWeek", kv.kpi_id, kv.kpi_value
      FROM metrics m
      CROSS JOIN LATERAL (
        VALUES
          ('LisaCount', m."LisaCount"::text),
          ('EmissionRate', m."EmissionRate"::text),
          ('B0Count', m."B0Count"::text),
          ('B1Count', m."B1Count"::text),
          ('Bm1Count', m."Bm1Count"::text),
          ('Bm2Count', m."Bm2Count"::text),
          ('NGCount', m."NGCount"::text),
          ('PGCount', m."PGCount"::text),
          ('Not_NGCount', m."Not_NGCount"::text),
          ('EmissionRateLPM', m."EmissionRateLPM"::text),
          ('RepresentativeEmissionRate', m."RepresentativeEmissionRate"::text),
          ('RepresentativeEmissionRateLPM', m."RepresentativeEmissionRateLPM"::text),
          ('B0RepEmissionRateLPM', m."B0RepEmissionRateLPM"::text),
          ('B1RepEmissionRateLPM', m."B1RepEmissionRateLPM"::text),
          ('Bm1RepEmissionRateLPM', m."Bm1RepEmissionRateLPM"::text),
          ('Bm2RepEmissionRateLPM', m."Bm2RepEmissionRateLPM"::text),
          ('B0RepEmissionRate', m."B0RepEmissionRate"::text),
          ('B1RepEmissionRate', m."B1RepEmissionRate"::text),
          ('Bm1RepEmissionRate', m."Bm1RepEmissionRate"::text),
          ('Bm2RepEmissionRate', m."Bm2RepEmissionRate"::text),
          ('LisaDensity', m."LisaDensity"::text),
          ('InstatanoeusEmission', m."InstatanoeusEmission"::text),
          ('InstatanoeusEmissionLPM', m."InstatanoeusEmissionLPM"::text),
          ('InstatanoeusRepEmission', m."InstatanoeusRepEmission"::text),
          ('InstatanoeusRepEmissionLPM', m."InstatanoeusRepEmissionLPM"::text),
          ('B0Density', m."B0Density"::text),
          ('B1Density', m."B1Density"::text),
          ('Bm1Density', m."Bm1Density"::text),
          ('Bm2Density', m."Bm2Density"::text),
          ('NGDensity', m."NGDensity"::text),
          ('PGDensity', m."PGDensity"::text),
          ('B0Share', m."B0Share"::text),
          ('B1Share', m."B1Share"::text),
          ('Bm1Share', m."Bm1Share"::text),
          ('Bm2Share', m."Bm2Share"::text),
          ('NGShare', m."NGShare"::text),
          ('PGShare', m."PGShare"::text),
          ('Not_NGShare', m."Not_NGShare"::text)
      ) AS kv(kpi_id, kpi_value)
      WHERE kv.kpi_value IS NOT NULL
    )
    SELECT
      kpihub.kpi_report_build_id(
        m.kpi_id, customer_name, m."ReportYear", m."ReportWeek",
        m."BoundaryRegion", p_period_type, p_include_boundary_region
      ),
      m.kpi_id, p_customer_id, m."BoundaryRegion", m."ReportYear",
      p_period_type, m."ReportWeek", m.kpi_value, data_type, NOW()
    FROM melted m;
  ELSE
    INSERT INTO kpihub."KPI_Data" (
      id, kpiid, customerid, boundaryregion, "Year", periodtype, periodvalue,
      "Value", datatype, lastupdated
    )
    WITH base AS (
      SELECT
        CASE
          WHEN p_include_boundary_region THEN r."BoundaryRegion"
          ELSE NULL::text
        END AS "BoundaryRegion",
        r."ReportYear",
        r."DistributionPipeCoveredKm",
        e."LisaCount",
        e."EmissionRate",
        e."B0Count",
        e."B1Count",
        e."Bm1Count",
        e."Bm2Count",
        e."NGCount",
        e."PGCount",
        e."Not_NGCount",
        e."EmissionRateLPM",
        e."RepresentativeEmissionRate",
        e."RepresentativeEmissionRateLPM",
        e."B0RepEmissionRateLPM",
        e."B1RepEmissionRateLPM",
        e."Bm1RepEmissionRateLPM",
        e."Bm2RepEmissionRateLPM",
        e."B0RepEmissionRate",
        e."B1RepEmissionRate",
        e."Bm1RepEmissionRate",
        e."Bm2RepEmissionRate"
      FROM kpihub."V_ReportSummary" r
      INNER JOIN kpihub."V_EmissionSourceSummary" e ON e."ReportId" = r."ReportId"
      WHERE r."CustomerId" = p_customer_id
    ),
    aggregated AS (
      SELECT
        "BoundaryRegion",
        "ReportYear",
        SUM("DistributionPipeCoveredKm") AS denom,
        ROUND(SUM("LisaCount")::numeric, 2) AS "LisaCount",
        ROUND(SUM("EmissionRate")::numeric, 2) AS "EmissionRate",
        ROUND(SUM("B0Count")::numeric, 2) AS "B0Count",
        ROUND(SUM("B1Count")::numeric, 2) AS "B1Count",
        ROUND(SUM("Bm1Count")::numeric, 2) AS "Bm1Count",
        ROUND(SUM("Bm2Count")::numeric, 2) AS "Bm2Count",
        ROUND(SUM("NGCount")::numeric, 2) AS "NGCount",
        ROUND(SUM("PGCount")::numeric, 2) AS "PGCount",
        ROUND(SUM("Not_NGCount")::numeric, 2) AS "Not_NGCount",
        ROUND(SUM("EmissionRateLPM")::numeric, 2) AS "EmissionRateLPM",
        ROUND(SUM("RepresentativeEmissionRate")::numeric, 2) AS "RepresentativeEmissionRate",
        ROUND(SUM("RepresentativeEmissionRateLPM")::numeric, 2) AS "RepresentativeEmissionRateLPM",
        ROUND(SUM("B0RepEmissionRateLPM")::numeric, 2) AS "B0RepEmissionRateLPM",
        ROUND(SUM("B1RepEmissionRateLPM")::numeric, 2) AS "B1RepEmissionRateLPM",
        ROUND(SUM("Bm1RepEmissionRateLPM")::numeric, 2) AS "Bm1RepEmissionRateLPM",
        ROUND(SUM("Bm2RepEmissionRateLPM")::numeric, 2) AS "Bm2RepEmissionRateLPM",
        ROUND(SUM("B0RepEmissionRate")::numeric, 2) AS "B0RepEmissionRate",
        ROUND(SUM("B1RepEmissionRate")::numeric, 2) AS "B1RepEmissionRate",
        ROUND(SUM("Bm1RepEmissionRate")::numeric, 2) AS "Bm1RepEmissionRate",
        ROUND(SUM("Bm2RepEmissionRate")::numeric, 2) AS "Bm2RepEmissionRate"
      FROM base
      GROUP BY "BoundaryRegion", "ReportYear"
    ),
    metrics AS (
      SELECT
        a.*,
        CASE WHEN denom > 0 THEN ROUND(("LisaCount" / denom)::numeric, 2) END AS "LisaDensity",
        CASE WHEN denom > 0 THEN ROUND(("EmissionRate" / denom)::numeric, 2) END AS "InstatanoeusEmission",
        CASE WHEN denom > 0 THEN ROUND(("EmissionRateLPM" / denom)::numeric, 2) END AS "InstatanoeusEmissionLPM",
        CASE WHEN denom > 0 THEN ROUND(("RepresentativeEmissionRate" / denom)::numeric, 2) END AS "InstatanoeusRepEmission",
        CASE WHEN denom > 0 THEN ROUND(("RepresentativeEmissionRateLPM" / denom)::numeric, 2) END AS "InstatanoeusRepEmissionLPM",
        CASE WHEN denom > 0 THEN ROUND(("B0Count" / denom)::numeric, 2) END AS "B0Density",
        CASE WHEN denom > 0 THEN ROUND(("B1Count" / denom)::numeric, 2) END AS "B1Density",
        CASE WHEN denom > 0 THEN ROUND(("Bm1Count" / denom)::numeric, 2) END AS "Bm1Density",
        CASE WHEN denom > 0 THEN ROUND(("Bm2Count" / denom)::numeric, 2) END AS "Bm2Density",
        CASE WHEN denom > 0 THEN ROUND(("NGCount" / denom)::numeric, 2) END AS "NGDensity",
        CASE WHEN denom > 0 THEN ROUND(("PGCount" / denom)::numeric, 2) END AS "PGDensity",
        CASE WHEN "LisaCount" > 0 THEN ROUND((100.0 * "B0Count" / "LisaCount")::numeric, 2) END AS "B0Share",
        CASE WHEN "LisaCount" > 0 THEN ROUND((100.0 * "B1Count" / "LisaCount")::numeric, 2) END AS "B1Share",
        CASE WHEN "LisaCount" > 0 THEN ROUND((100.0 * "Bm1Count" / "LisaCount")::numeric, 2) END AS "Bm1Share",
        CASE WHEN "LisaCount" > 0 THEN ROUND((100.0 * "Bm2Count" / "LisaCount")::numeric, 2) END AS "Bm2Share",
        CASE WHEN ("NGCount" + "Not_NGCount" + "PGCount") > 0
          THEN ROUND((100.0 * "NGCount" / ("NGCount" + "Not_NGCount" + "PGCount"))::numeric, 2)
        END AS "NGShare",
        CASE WHEN ("NGCount" + "Not_NGCount" + "PGCount") > 0
          THEN ROUND((100.0 * "PGCount" / ("NGCount" + "Not_NGCount" + "PGCount"))::numeric, 2)
        END AS "PGShare",
        CASE WHEN ("NGCount" + "Not_NGCount" + "PGCount") > 0
          THEN ROUND((100.0 * "Not_NGCount" / ("NGCount" + "Not_NGCount" + "PGCount"))::numeric, 2)
        END AS "Not_NGShare"
      FROM aggregated a
    ),
    melted AS (
      SELECT m."BoundaryRegion", m."ReportYear", kv.kpi_id, kv.kpi_value
      FROM metrics m
      CROSS JOIN LATERAL (
        VALUES
          ('LisaCount', m."LisaCount"::text),
          ('EmissionRate', m."EmissionRate"::text),
          ('B0Count', m."B0Count"::text),
          ('B1Count', m."B1Count"::text),
          ('Bm1Count', m."Bm1Count"::text),
          ('Bm2Count', m."Bm2Count"::text),
          ('NGCount', m."NGCount"::text),
          ('PGCount', m."PGCount"::text),
          ('Not_NGCount', m."Not_NGCount"::text),
          ('EmissionRateLPM', m."EmissionRateLPM"::text),
          ('RepresentativeEmissionRate', m."RepresentativeEmissionRate"::text),
          ('RepresentativeEmissionRateLPM', m."RepresentativeEmissionRateLPM"::text),
          ('B0RepEmissionRateLPM', m."B0RepEmissionRateLPM"::text),
          ('B1RepEmissionRateLPM', m."B1RepEmissionRateLPM"::text),
          ('Bm1RepEmissionRateLPM', m."Bm1RepEmissionRateLPM"::text),
          ('Bm2RepEmissionRateLPM', m."Bm2RepEmissionRateLPM"::text),
          ('B0RepEmissionRate', m."B0RepEmissionRate"::text),
          ('B1RepEmissionRate', m."B1RepEmissionRate"::text),
          ('Bm1RepEmissionRate', m."Bm1RepEmissionRate"::text),
          ('Bm2RepEmissionRate', m."Bm2RepEmissionRate"::text),
          ('LisaDensity', m."LisaDensity"::text),
          ('InstatanoeusEmission', m."InstatanoeusEmission"::text),
          ('InstatanoeusEmissionLPM', m."InstatanoeusEmissionLPM"::text),
          ('InstatanoeusRepEmission', m."InstatanoeusRepEmission"::text),
          ('InstatanoeusRepEmissionLPM', m."InstatanoeusRepEmissionLPM"::text),
          ('B0Density', m."B0Density"::text),
          ('B1Density', m."B1Density"::text),
          ('Bm1Density', m."Bm1Density"::text),
          ('Bm2Density', m."Bm2Density"::text),
          ('NGDensity', m."NGDensity"::text),
          ('PGDensity', m."PGDensity"::text),
          ('B0Share', m."B0Share"::text),
          ('B1Share', m."B1Share"::text),
          ('Bm1Share', m."Bm1Share"::text),
          ('Bm2Share', m."Bm2Share"::text),
          ('NGShare', m."NGShare"::text),
          ('PGShare', m."PGShare"::text),
          ('Not_NGShare', m."Not_NGShare"::text)
      ) AS kv(kpi_id, kpi_value)
      WHERE kv.kpi_value IS NOT NULL
    )
    SELECT
      kpihub.kpi_report_build_id(
        m.kpi_id, customer_name, m."ReportYear", NULL,
        m."BoundaryRegion", p_period_type, p_include_boundary_region
      ),
      m.kpi_id, p_customer_id, m."BoundaryRegion", m."ReportYear",
      p_period_type, NULL, m.kpi_value, data_type, NOW()
    FROM melted m;
  END IF;
END;
$$;

CREATE OR REPLACE PROCEDURE kpihub.refresh_kpi_emission_source_customer_all(
  p_customer_id uuid
)
LANGUAGE plpgsql
AS $$
BEGIN
  CALL kpihub.refresh_kpi_emission_source_customer(p_customer_id, false, 'Week');
  CALL kpihub.refresh_kpi_emission_source_customer(p_customer_id, true, 'Week');
  CALL kpihub.refresh_kpi_emission_source_customer(p_customer_id, false, 'Year');
  CALL kpihub.refresh_kpi_emission_source_customer(p_customer_id, true, 'Year');
END;
$$;

CREATE OR REPLACE PROCEDURE kpihub.refresh_kpi_emission_source()
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
    CALL kpihub.refresh_kpi_emission_source_customer_all(cust.customerid);
  END LOOP;
END;
$$;

COMMENT ON PROCEDURE kpihub.refresh_kpi_emission_source_customer(uuid, boolean, text) IS
  'Compute KPIEmissionSource metrics from V_ReportSummary + V_EmissionSourceSummary.';

COMMENT ON PROCEDURE kpihub.refresh_kpi_emission_source() IS
  'Refresh KPIEmissionSource KPIs (weekly/yearly, global/regional) for all active customers.';
