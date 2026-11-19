-- KPISurveySummary processor mirroring SQLite/lib/kpi_processor/KPIReport.py
--
-- Joins kpihub."V_ReportSummary" with kpihub."V_SurveySummary", aggregates per
-- customer, and writes melted rows to kpihub."KPI_Data".
--
-- Prerequisite:
--   1. IngesterTables.sql, SeedCustomerInfo.sql
--   2. ReportSummary.sql + SurveySummaryMaterializedView.sql refreshed
--   3. KPIReport.sql (reuses kpihub.kpi_report_build_id)
--
-- Setup:
--   psql -U dsoler -d Datanalytics -v ON_ERROR_STOP=1 -f KPISurveySummary.sql
--
-- Refresh:
--   CALL kpihub.refresh_kpi_survey_summary_customer('<customer-id>'::uuid);
--   CALL kpihub.refresh_kpi_survey_summary();

DO $$
BEGIN
  ALTER TABLE kpihub."KPI_Data"
    ALTER COLUMN periodtype TYPE TEXT USING periodtype::text;
EXCEPTION
  WHEN others THEN
    NULL;
END $$;

CREATE OR REPLACE FUNCTION kpihub.kpi_days_in_week_range(
  p_week_number integer,
  p_year integer,
  p_max_days integer DEFAULT 7
)
RETURNS integer
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
  start_date date;
  delta integer;
BEGIN
  BEGIN
    start_date := to_date(
      p_year::text || lpad(p_week_number::text, 2, '0') || '1',
      'IYYYIWID'
    );
  EXCEPTION
    WHEN others THEN
      RETURN p_max_days;
  END;

  IF p_year = EXTRACT(isoyear FROM CURRENT_DATE)::integer
     AND p_week_number = EXTRACT(week FROM CURRENT_DATE)::integer THEN
    delta := (CURRENT_DATE - start_date)::integer + 1;
    RETURN LEAST(GREATEST(delta, 0), 7);
  END IF;

  RETURN p_max_days;
END;
$$;

CREATE OR REPLACE PROCEDURE kpihub.refresh_kpi_survey_summary_customer(
  p_customer_id uuid,
  p_include_boundary_region boolean DEFAULT false,
  p_period_type text DEFAULT 'Week'
)
LANGUAGE plpgsql
AS $$
DECLARE
  customer_name text;
  data_type text;
  base_kpi_ids text[] := ARRAY[
    'SurveyDurationHours', 'StarndardUtilization', 'TotalSurveyors',
    'ProductivityPerSurveyor', 'SurveyCount', 'AvgSpeedKm', 'IdleTime',
    'TotalDrivenLengthKm', 'DrivingRatio', 'NightDrivenLength', 'DayDrivenLength',
    'NightRatio', 'DayRatio'
  ];
  weekly_kpi_ids text[] := ARRAY[
    'TargetDurationHours', 'CustomerUtilization', 'SurveysCarDay', 'DaysCount'
  ];
  kpi_ids text[];
BEGIN
  IF p_period_type NOT IN ('Week', 'Year') THEN
    RAISE EXCEPTION 'Unsupported period type: % (expected Week or Year)', p_period_type;
  END IF;

  kpi_ids := base_kpi_ids;
  IF p_period_type = 'Week' THEN
    kpi_ids := kpi_ids || weekly_kpi_ids;
  END IF;

  SELECT "Name"
  INTO customer_name
  FROM kpihub."KPI_Customer"
  WHERE customerid = p_customer_id;

  IF customer_name IS NULL THEN
    RAISE EXCEPTION 'Customer % not found in KPI_Customer', p_customer_id;
  END IF;

  data_type := CASE
    WHEN p_include_boundary_region THEN 'KPISurveySummaryRegional'
    ELSE 'KPISurveySummaryGlobal'
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
    WITH utilization AS (
      SELECT
        u.workingdays,
        u.workinghours
      FROM kpihub."KPI_Utilization" u
      WHERE u.customerid = p_customer_id
    ),
    base AS (
      SELECT
        CASE
          WHEN p_include_boundary_region THEN r."BoundaryRegion"
          ELSE NULL::text
        END AS "BoundaryRegion",
        r."ReportYear",
        r."ReportWeek",
        r."ReportId",
        r."DistributionPipeCoveredKm",
        r."AssetCoveredLengthKm",
        s."SurveyId",
        s."SurveyorUnit",
        s."SurveyDurationMinutes",
        s."IdleTimeMinutes",
        s."TotalKilometers",
        s."NightKilometers",
        s."DayKilometers",
        s."AvgSpeedKm",
        s."TotalSegments"
      FROM kpihub."V_ReportSummary" r
      INNER JOIN kpihub."V_SurveySummary" s ON s."ReportId" = r."ReportId"
      WHERE r."CustomerId" = p_customer_id
    ),
    report_unique AS (
      SELECT DISTINCT
        "BoundaryRegion",
        "ReportYear",
        "ReportWeek",
        "ReportId",
        "DistributionPipeCoveredKm",
        "AssetCoveredLengthKm"
      FROM base
    ),
    aggregated AS (
      SELECT
        b."BoundaryRegion",
        b."ReportYear",
        b."ReportWeek",
        SUM(b."SurveyDurationMinutes") AS survey_duration_minutes,
        COUNT(DISTINCT b."SurveyorUnit") AS total_surveyors,
        COUNT(DISTINCT b."SurveyId") AS survey_count,
        SUM(b."AvgSpeedKm" * b."TotalSegments") AS weighted_speed_num,
        SUM(b."TotalSegments") AS total_segments,
        SUM(b."IdleTimeMinutes") AS idle_time_minutes,
        SUM(b."TotalKilometers") AS total_kilometers,
        SUM(b."NightKilometers") AS night_kilometers,
        SUM(b."DayKilometers") AS day_kilometers
      FROM base b
      GROUP BY b."BoundaryRegion", b."ReportYear", b."ReportWeek"
    ),
    report_totals AS (
      SELECT
        "BoundaryRegion",
        "ReportYear",
        "ReportWeek",
        SUM("DistributionPipeCoveredKm") AS distribution_pipe_covered_km,
        SUM("AssetCoveredLengthKm") AS asset_covered_length_km
      FROM report_unique
      GROUP BY "BoundaryRegion", "ReportYear", "ReportWeek"
    ),
    metrics AS (
      SELECT
        a."BoundaryRegion",
        a."ReportYear",
        a."ReportWeek",
        ROUND((a.survey_duration_minutes / 60.0)::numeric, 2) AS "SurveyDurationHours",
        CASE
          WHEN a.total_surveyors > 0 THEN
            ROUND((100.0 * (a.survey_duration_minutes / 60.0) / (6.0 * 5.0 * a.total_surveyors))::numeric, 2)
        END AS "StarndardUtilization",
        a.total_surveyors AS "TotalSurveyors",
        CASE
          WHEN a.total_surveyors > 0 THEN
            ROUND((rt.distribution_pipe_covered_km / a.total_surveyors)::numeric, 2)
        END AS "ProductivityPerSurveyor",
        a.survey_count AS "SurveyCount",
        CASE
          WHEN a.total_segments > 0 THEN
            ROUND((a.weighted_speed_num / a.total_segments)::numeric, 2)
        END AS "AvgSpeedKm",
        CASE
          WHEN a.survey_duration_minutes > 0 THEN
            ROUND((100.0 * a.idle_time_minutes / a.survey_duration_minutes)::numeric, 2)
        END AS "IdleTime",
        ROUND(a.total_kilometers::numeric, 2) AS "TotalDrivenLengthKm",
        CASE
          WHEN rt.asset_covered_length_km > 0 THEN
            ROUND((a.total_kilometers / rt.asset_covered_length_km)::numeric, 2)
        END AS "DrivingRatio",
        ROUND(a.night_kilometers::numeric, 2) AS "NightDrivenLength",
        ROUND(a.day_kilometers::numeric, 2) AS "DayDrivenLength",
        CASE
          WHEN a.total_kilometers > 0 THEN
            ROUND((100.0 * a.night_kilometers / a.total_kilometers)::numeric, 2)
        END AS "NightRatio",
        CASE
          WHEN a.total_kilometers > 0 THEN
            ROUND((100.0 * a.day_kilometers / a.total_kilometers)::numeric, 2)
        END AS "DayRatio",
        kpihub.kpi_days_in_week_range(
          a."ReportWeek",
          a."ReportYear",
          u.workingdays
        ) AS "DaysCount",
        CASE
          WHEN a.total_surveyors > 0 THEN
            ROUND((
              kpihub.kpi_days_in_week_range(a."ReportWeek", a."ReportYear", u.workingdays)
              * u.workinghours
              * a.total_surveyors
            )::numeric, 2)
        END AS "TargetDurationHours",
        CASE
          WHEN a.total_surveyors > 0
           AND kpihub.kpi_days_in_week_range(a."ReportWeek", a."ReportYear", u.workingdays) > 0
           AND u.workinghours > 0 THEN
            ROUND((
              100.0 * (a.survey_duration_minutes / 60.0)
              / (
                kpihub.kpi_days_in_week_range(a."ReportWeek", a."ReportYear", u.workingdays)
                * u.workinghours
                * a.total_surveyors
              )
            )::numeric, 2)
        END AS "CustomerUtilization",
        CASE
          WHEN a.total_surveyors > 0
           AND kpihub.kpi_days_in_week_range(a."ReportWeek", a."ReportYear", u.workingdays) > 0 THEN
            ROUND((
              a.survey_count::numeric
              / a.total_surveyors
              / kpihub.kpi_days_in_week_range(a."ReportWeek", a."ReportYear", u.workingdays)
            )::numeric, 2)
        END AS "SurveysCarDay"
      FROM aggregated a
      INNER JOIN report_totals rt
        ON rt."BoundaryRegion" IS NOT DISTINCT FROM a."BoundaryRegion"
       AND rt."ReportYear" = a."ReportYear"
       AND rt."ReportWeek" = a."ReportWeek"
      CROSS JOIN utilization u
    ),
    melted AS (
      SELECT m."BoundaryRegion", m."ReportYear", m."ReportWeek", kv.kpi_id, kv.kpi_value
      FROM metrics m
      CROSS JOIN LATERAL (
        VALUES
          ('SurveyDurationHours', m."SurveyDurationHours"::text),
          ('StarndardUtilization', m."StarndardUtilization"::text),
          ('TotalSurveyors', m."TotalSurveyors"::text),
          ('ProductivityPerSurveyor', m."ProductivityPerSurveyor"::text),
          ('SurveyCount', m."SurveyCount"::text),
          ('AvgSpeedKm', m."AvgSpeedKm"::text),
          ('IdleTime', m."IdleTime"::text),
          ('TotalDrivenLengthKm', m."TotalDrivenLengthKm"::text),
          ('DrivingRatio', m."DrivingRatio"::text),
          ('NightDrivenLength', m."NightDrivenLength"::text),
          ('DayDrivenLength', m."DayDrivenLength"::text),
          ('NightRatio', m."NightRatio"::text),
          ('DayRatio', m."DayRatio"::text),
          ('TargetDurationHours', m."TargetDurationHours"::text),
          ('CustomerUtilization', m."CustomerUtilization"::text),
          ('SurveysCarDay', m."SurveysCarDay"::text),
          ('DaysCount', m."DaysCount"::text)
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
        r."ReportId",
        r."DistributionPipeCoveredKm",
        r."AssetCoveredLengthKm",
        s."SurveyId",
        s."SurveyorUnit",
        s."SurveyDurationMinutes",
        s."IdleTimeMinutes",
        s."TotalKilometers",
        s."NightKilometers",
        s."DayKilometers",
        s."AvgSpeedKm",
        s."TotalSegments"
      FROM kpihub."V_ReportSummary" r
      INNER JOIN kpihub."V_SurveySummary" s ON s."ReportId" = r."ReportId"
      WHERE r."CustomerId" = p_customer_id
    ),
    report_unique AS (
      SELECT DISTINCT
        "BoundaryRegion",
        "ReportYear",
        "ReportId",
        "DistributionPipeCoveredKm",
        "AssetCoveredLengthKm"
      FROM base
    ),
    aggregated AS (
      SELECT
        b."BoundaryRegion",
        b."ReportYear",
        SUM(b."SurveyDurationMinutes") AS survey_duration_minutes,
        COUNT(DISTINCT b."SurveyorUnit") AS total_surveyors,
        COUNT(DISTINCT b."SurveyId") AS survey_count,
        SUM(b."AvgSpeedKm" * b."TotalSegments") AS weighted_speed_num,
        SUM(b."TotalSegments") AS total_segments,
        SUM(b."IdleTimeMinutes") AS idle_time_minutes,
        SUM(b."TotalKilometers") AS total_kilometers,
        SUM(b."NightKilometers") AS night_kilometers,
        SUM(b."DayKilometers") AS day_kilometers
      FROM base b
      GROUP BY b."BoundaryRegion", b."ReportYear"
    ),
    report_totals AS (
      SELECT
        "BoundaryRegion",
        "ReportYear",
        SUM("DistributionPipeCoveredKm") AS distribution_pipe_covered_km,
        SUM("AssetCoveredLengthKm") AS asset_covered_length_km
      FROM report_unique
      GROUP BY "BoundaryRegion", "ReportYear"
    ),
    metrics AS (
      SELECT
        a."BoundaryRegion",
        a."ReportYear",
        ROUND((a.survey_duration_minutes / 60.0)::numeric, 2) AS "SurveyDurationHours",
        CASE
          WHEN a.total_surveyors > 0 THEN
            ROUND((100.0 * (a.survey_duration_minutes / 60.0) / (6.0 * 5.0 * a.total_surveyors))::numeric, 2)
        END AS "StarndardUtilization",
        a.total_surveyors AS "TotalSurveyors",
        CASE
          WHEN a.total_surveyors > 0 THEN
            ROUND((rt.distribution_pipe_covered_km / a.total_surveyors)::numeric, 2)
        END AS "ProductivityPerSurveyor",
        a.survey_count AS "SurveyCount",
        CASE
          WHEN a.total_segments > 0 THEN
            ROUND((a.weighted_speed_num / a.total_segments)::numeric, 2)
        END AS "AvgSpeedKm",
        CASE
          WHEN a.survey_duration_minutes > 0 THEN
            ROUND((100.0 * a.idle_time_minutes / a.survey_duration_minutes)::numeric, 2)
        END AS "IdleTime",
        ROUND(a.total_kilometers::numeric, 2) AS "TotalDrivenLengthKm",
        CASE
          WHEN rt.asset_covered_length_km > 0 THEN
            ROUND((a.total_kilometers / rt.asset_covered_length_km)::numeric, 2)
        END AS "DrivingRatio",
        ROUND(a.night_kilometers::numeric, 2) AS "NightDrivenLength",
        ROUND(a.day_kilometers::numeric, 2) AS "DayDrivenLength",
        CASE
          WHEN a.total_kilometers > 0 THEN
            ROUND((100.0 * a.night_kilometers / a.total_kilometers)::numeric, 2)
        END AS "NightRatio",
        CASE
          WHEN a.total_kilometers > 0 THEN
            ROUND((100.0 * a.day_kilometers / a.total_kilometers)::numeric, 2)
        END AS "DayRatio"
      FROM aggregated a
      INNER JOIN report_totals rt
        ON rt."BoundaryRegion" IS NOT DISTINCT FROM a."BoundaryRegion"
       AND rt."ReportYear" = a."ReportYear"
    ),
    melted AS (
      SELECT m."BoundaryRegion", m."ReportYear", kv.kpi_id, kv.kpi_value
      FROM metrics m
      CROSS JOIN LATERAL (
        VALUES
          ('SurveyDurationHours', m."SurveyDurationHours"::text),
          ('StarndardUtilization', m."StarndardUtilization"::text),
          ('TotalSurveyors', m."TotalSurveyors"::text),
          ('ProductivityPerSurveyor', m."ProductivityPerSurveyor"::text),
          ('SurveyCount', m."SurveyCount"::text),
          ('AvgSpeedKm', m."AvgSpeedKm"::text),
          ('IdleTime', m."IdleTime"::text),
          ('TotalDrivenLengthKm', m."TotalDrivenLengthKm"::text),
          ('DrivingRatio', m."DrivingRatio"::text),
          ('NightDrivenLength', m."NightDrivenLength"::text),
          ('DayDrivenLength', m."DayDrivenLength"::text),
          ('NightRatio', m."NightRatio"::text),
          ('DayRatio', m."DayRatio"::text)
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

CREATE OR REPLACE PROCEDURE kpihub.refresh_kpi_survey_summary_customer_all(
  p_customer_id uuid
)
LANGUAGE plpgsql
AS $$
BEGIN
  CALL kpihub.refresh_kpi_survey_summary_customer(p_customer_id, false, 'Week');
  CALL kpihub.refresh_kpi_survey_summary_customer(p_customer_id, true, 'Week');
  CALL kpihub.refresh_kpi_survey_summary_customer(p_customer_id, false, 'Year');
  CALL kpihub.refresh_kpi_survey_summary_customer(p_customer_id, true, 'Year');
END;
$$;

CREATE OR REPLACE PROCEDURE kpihub.refresh_kpi_survey_summary()
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
    CALL kpihub.refresh_kpi_survey_summary_customer_all(cust.customerid);
  END LOOP;
END;
$$;

COMMENT ON FUNCTION kpihub.kpi_days_in_week_range(integer, integer, integer) IS
  'Mirror KPIReport.days_in_week_range for weekly utilization KPIs.';

COMMENT ON PROCEDURE kpihub.refresh_kpi_survey_summary_customer(uuid, boolean, text) IS
  'Compute KPISurveySummary metrics from V_ReportSummary + V_SurveySummary.';

COMMENT ON PROCEDURE kpihub.refresh_kpi_survey_summary() IS
  'Refresh KPISurveySummary KPIs (weekly/yearly, global/regional) for all active customers.';
