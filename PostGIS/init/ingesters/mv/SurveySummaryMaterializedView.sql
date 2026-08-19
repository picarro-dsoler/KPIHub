-- Survey summary per (SurveyId, ReportId) for reports in
-- kpihub."MV_ReportSummary_eu1" / eu2. Reports with no driving surveys get one
-- zero-valued placeholder row (sentinel SurveyId). Surveys with no in-area
-- segments still get a row with zero segment metrics.
--
-- Config mirrors lib/config.py: SUNRISE_TIME=6, SUNSET_TIME=20, SPEED_THRESHOLD=0.5
--
-- Prerequisite:
--   1. IngesterTables.sql, SeedCustomerInfo.sql
--   2. ReportSummary.sql + REFRESH MATERIALIZED VIEW kpihub."MV_ReportSummary_eu1";
--      REFRESH MATERIALIZED VIEW kpihub."MV_ReportSummary_eu2";
--   3. SegmentCacheMaterializedView.sql (refresh cache before survey summary)
--
-- Recommended refresh order per customer:
--   CALL kpihub.refresh_segment_cache_customer('<customer-id>'::uuid, 'EU1');
--   CALL kpihub.refresh_survey_summary_customer('<customer-id>'::uuid, 'EU1');
--
-- Setup:
--   psql -U dsoler -d Datanalytics -v ON_ERROR_STOP=1 -f SurveySummaryMaterializedView.sql
--
-- Load / refresh (batched per customer; optional single-report via refresh_survey_summary_report):
--   CALL kpihub.refresh_survey_summary_report('<report-id>'::uuid, 'EU1');
--   CALL kpihub.refresh_survey_summary_customer('<customer-id>'::uuid, 'EU1');
--   CALL kpihub.refresh_survey_summary();

SET enable_mergejoin = off;
SET work_mem = '256MB';
SET maintenance_work_mem = '512MB';

DROP VIEW IF EXISTS kpihub."V_SurveySummary";
DROP TABLE IF EXISTS kpihub."MV_SurveySummary_eu1";
DROP TABLE IF EXISTS kpihub."MV_SurveySummary_eu2";

CREATE TABLE kpihub."MV_SurveySummary_eu1" (
  "SurveyId" uuid NOT NULL,
  "ReportId" uuid NOT NULL,
  "SurveyorUnit" text,
  "SurveyDurationMinutes" double precision,
  "SurveyRawDurationMinutes" double precision,
  "SegmentWeight" double precision,
  "StartHour" integer,
  "StartTime" timestamp,
  "StartEpoch" bigint,
  "EndTime" timestamp,
  "EndEpoch" bigint,
  "StartDay" date,
  "EndDay" date,
  "LateralRotation" text,
  "NumberOfPeaks" integer,
  "DaySegments" integer,
  "NightSegments" integer,
  "ActiveSegments" integer,
  "IdleSegments" integer,
  "TotalSegments" integer,
  "TotalSegmentsInSurvey" integer,
  "TotalKilometers" double precision,
  "DayKilometers" double precision,
  "NightKilometers" double precision,
  "IdleTimeMinutes" double precision,
  "ActiveTimeMinutes" double precision,
  "SegmentDurationMinutes" double precision,
  "AvgSpeedKm" double precision,
  "LastUpdated" timestamp,
  PRIMARY KEY ("SurveyId", "ReportId")
);

CREATE TABLE kpihub."MV_SurveySummary_eu2" (
  LIKE kpihub."MV_SurveySummary_eu1" INCLUDING ALL
);

CREATE INDEX IF NOT EXISTS "MV_SurveySummary_eu1_ReportId_idx"
  ON kpihub."MV_SurveySummary_eu1" ("ReportId");

CREATE INDEX IF NOT EXISTS "MV_SurveySummary_eu2_ReportId_idx"
  ON kpihub."MV_SurveySummary_eu2" ("ReportId");

DROP PROCEDURE IF EXISTS kpihub.refresh_survey_summary();
DROP PROCEDURE IF EXISTS kpihub.refresh_survey_summary_report(uuid, text);
DROP PROCEDURE IF EXISTS kpihub.refresh_survey_summary_customer(uuid, text);
DROP PROCEDURE IF EXISTS kpihub.refresh_survey_summary_customer(uuid, text, uuid);

CREATE OR REPLACE PROCEDURE kpihub.refresh_survey_summary_customer(
  p_customer_id uuid,
  p_db_location text,
  p_report_id uuid DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
DECLARE
  lsdb_schema text;
  report_table text;
  target_table text;
  cache_table text;
  cache_survey_table text;
  zero_survey_id constant uuid := '00000000-0000-0000-0000-000000000000';
BEGIN
  SET LOCAL enable_mergejoin = off;
  SET LOCAL work_mem = '1GB';

  IF upper(p_db_location) = 'EU2' THEN
    lsdb_schema := 'eu2';
    report_table := 'kpihub."MV_ReportSummary_eu2"';
    target_table := 'kpihub."MV_SurveySummary_eu2"';
    cache_table := 'kpihub."SegmentCache_eu2"';
    cache_survey_table := 'kpihub."SegmentCacheSurvey_eu2"';
  ELSIF upper(p_db_location) = 'EU1' THEN
    lsdb_schema := 'eu1';
    report_table := 'kpihub."MV_ReportSummary_eu1"';
    target_table := 'kpihub."MV_SurveySummary_eu1"';
    cache_table := 'kpihub."SegmentCache_eu1"';
    cache_survey_table := 'kpihub."SegmentCacheSurvey_eu1"';
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
        AND ($2::uuid IS NULL OR "ReportId" = $2)
    )
    $sql$,
    target_table,
    report_table
  ) USING p_customer_id, p_report_id;

  EXECUTE format(
    $sql$
    INSERT INTO %s (
      "SurveyId",
      "ReportId",
      "SurveyorUnit",
      "SurveyDurationMinutes",
      "SurveyRawDurationMinutes",
      "SegmentWeight",
      "StartHour",
      "StartTime",
      "StartEpoch",
      "EndTime",
      "EndEpoch",
      "StartDay",
      "EndDay",
      "LateralRotation",
      "NumberOfPeaks",
      "DaySegments",
      "NightSegments",
      "ActiveSegments",
      "IdleSegments",
      "TotalSegments",
      "TotalSegmentsInSurvey",
      "TotalKilometers",
      "DayKilometers",
      "NightKilometers",
      "IdleTimeMinutes",
      "ActiveTimeMinutes",
      "SegmentDurationMinutes",
      "AvgSpeedKm",
      "LastUpdated"
    )
    WITH customer_reports AS (
      SELECT
        "ReportId",
        "ReportArea"
      FROM %s
      WHERE "CustomerId" = $1
        AND ($2::uuid IS NULL OR "ReportId" = $2)
    ),
    report_surveys AS (
      SELECT
        S."Id"::uuid AS "SurveyId",
        cr."ReportId",
        cr."ReportArea",
        SU."Description" AS "SurveyorUnit",
        (S."EndEpoch" - S."StartEpoch") / 60.0 AS "SurveyRawDurationMinutes",
        EXTRACT(HOUR FROM to_timestamp(S."StartEpoch"))::int AS "StartHour",
        to_timestamp(S."StartEpoch") AS "StartTime",
        S."StartEpoch"::bigint AS "StartEpoch",
        to_timestamp(S."EndEpoch") AS "EndTime",
        S."EndEpoch"::bigint AS "EndEpoch",
        to_timestamp(S."StartEpoch")::date AS "StartDay",
        to_timestamp(S."EndEpoch")::date AS "EndDay",
        SQC."LateralRotation"::text AS "LateralRotation",
        SQC."NumberOfPeaks"::int AS "NumberOfPeaks"
      FROM customer_reports cr
      INNER JOIN %I."ReportDrivingSurvey" RDS
        ON upper(RDS."ReportId") = upper(cr."ReportId"::text)
      INNER JOIN %I."Survey" S ON S."Id" = RDS."SurveyId"
      LEFT JOIN %I."SurveyQACheck" SQC ON S."Id" = SQC."SurveyId"
      LEFT JOIN %I."SurveyorUnit" SU ON S."SurveyorUnitId" = SU."Id"
    ),
    segments_with_totals AS (
      SELECT
        rs."SurveyId",
        rs."ReportId",
        rs."ReportArea",
        seg."LengthMeters",
        seg."DurationSeconds",
        seg."CarSpeedMedian",
        seg."StartEpoch",
        seg."Shape",
        cs."SegmentCount" AS "TotalSegmentsInSurvey"
      FROM report_surveys rs
      INNER JOIN %s cs
        ON cs."SurveyId" = upper(rs."SurveyId"::text)
      INNER JOIN %s seg
        ON seg."SurveyId" = upper(rs."SurveyId"::text)
    ),
    segments_filtered AS (
      SELECT
        "SurveyId",
        "ReportId",
        "LengthMeters",
        "DurationSeconds",
        "CarSpeedMedian",
        "TotalSegmentsInSurvey",
        CASE
          WHEN EXTRACT(HOUR FROM to_timestamp("StartEpoch")) >= 6
           AND EXTRACT(HOUR FROM to_timestamp("StartEpoch")) < 20
          THEN 'Day'
          ELSE 'Night'
        END AS day_night,
        CASE
          WHEN COALESCE("CarSpeedMedian", 0) < 0.5 THEN 'Idle'
          ELSE 'Active'
        END AS active_idle
      FROM segments_with_totals
      WHERE "ReportArea" IS NULL
        OR (
          "Shape" IS NOT NULL
          AND "Shape" && ST_Envelope("ReportArea")
          AND ST_Intersects("Shape", "ReportArea")
        )
    ),
    segment_agg AS (
      SELECT
        "SurveyId",
        "ReportId",
        MAX("TotalSegmentsInSurvey") AS "TotalSegmentsInSurvey",
        COUNT(*) FILTER (WHERE day_night = 'Day')::int AS "DaySegments",
        COUNT(*) FILTER (WHERE day_night = 'Night')::int AS "NightSegments",
        COUNT(*) FILTER (WHERE active_idle = 'Active')::int AS "ActiveSegments",
        COUNT(*) FILTER (WHERE active_idle = 'Idle')::int AS "IdleSegments",
        COUNT(*)::int AS "TotalSegments",
        COALESCE(SUM("LengthMeters"), 0) / 1000.0 AS "TotalKilometers",
        COALESCE(SUM("LengthMeters") FILTER (WHERE day_night = 'Day'), 0) / 1000.0 AS "DayKilometers",
        COALESCE(SUM("LengthMeters") FILTER (WHERE day_night = 'Night'), 0) / 1000.0 AS "NightKilometers",
        COALESCE(SUM("DurationSeconds"), 0) / 60.0 AS "SegmentDurationMinutes",
        COALESCE(SUM("DurationSeconds") FILTER (WHERE active_idle = 'Idle'), 0) / 60.0 AS "IdleTimeMinutes",
        COALESCE(SUM("DurationSeconds") FILTER (WHERE active_idle = 'Active'), 0) / 60.0 AS "ActiveTimeMinutes",
        3.6 * AVG("CarSpeedMedian") AS "AvgSpeedKm"
      FROM segments_filtered
      GROUP BY "SurveyId", "ReportId"
    )
    SELECT
      rs."SurveyId",
      rs."ReportId",
      rs."SurveyorUnit",
      COALESCE(
        rs."SurveyRawDurationMinutes"
          * (COALESCE(sa."TotalSegments", 0)::double precision
             / NULLIF(COALESCE(sa."TotalSegmentsInSurvey", 0), 0)),
        0
      ) AS "SurveyDurationMinutes",
      COALESCE(rs."SurveyRawDurationMinutes", 0) AS "SurveyRawDurationMinutes",
      COALESCE(
        COALESCE(sa."TotalSegments", 0)::double precision
          / NULLIF(COALESCE(sa."TotalSegmentsInSurvey", 0), 0),
        0
      ) AS "SegmentWeight",
      rs."StartHour",
      rs."StartTime",
      rs."StartEpoch",
      rs."EndTime",
      rs."EndEpoch",
      rs."StartDay",
      rs."EndDay",
      rs."LateralRotation",
      COALESCE(rs."NumberOfPeaks", 0) AS "NumberOfPeaks",
      COALESCE(sa."DaySegments", 0) AS "DaySegments",
      COALESCE(sa."NightSegments", 0) AS "NightSegments",
      COALESCE(sa."ActiveSegments", 0) AS "ActiveSegments",
      COALESCE(sa."IdleSegments", 0) AS "IdleSegments",
      COALESCE(sa."TotalSegments", 0) AS "TotalSegments",
      COALESCE(sa."TotalSegmentsInSurvey", 0) AS "TotalSegmentsInSurvey",
      COALESCE(sa."TotalKilometers", 0) AS "TotalKilometers",
      COALESCE(sa."DayKilometers", 0) AS "DayKilometers",
      COALESCE(sa."NightKilometers", 0) AS "NightKilometers",
      COALESCE(sa."IdleTimeMinutes", 0) AS "IdleTimeMinutes",
      COALESCE(sa."ActiveTimeMinutes", 0) AS "ActiveTimeMinutes",
      COALESCE(sa."SegmentDurationMinutes", 0) AS "SegmentDurationMinutes",
      COALESCE(sa."AvgSpeedKm", 0) AS "AvgSpeedKm",
      NOW() AS "LastUpdated"
    FROM report_surveys rs
    LEFT JOIN segment_agg sa
      ON rs."SurveyId" = sa."SurveyId"
     AND rs."ReportId" = sa."ReportId"
    $sql$,
    target_table,
    report_table,
    lsdb_schema,
    lsdb_schema,
    lsdb_schema,
    lsdb_schema,
    cache_survey_table,
    cache_table
  ) USING p_customer_id, p_report_id;

  EXECUTE format(
    $sql$
    INSERT INTO %s (
      "SurveyId",
      "ReportId",
      "SurveyorUnit",
      "SurveyDurationMinutes",
      "SurveyRawDurationMinutes",
      "SegmentWeight",
      "StartHour",
      "StartTime",
      "StartEpoch",
      "EndTime",
      "EndEpoch",
      "StartDay",
      "EndDay",
      "LateralRotation",
      "NumberOfPeaks",
      "DaySegments",
      "NightSegments",
      "ActiveSegments",
      "IdleSegments",
      "TotalSegments",
      "TotalSegmentsInSurvey",
      "TotalKilometers",
      "DayKilometers",
      "NightKilometers",
      "IdleTimeMinutes",
      "ActiveTimeMinutes",
      "SegmentDurationMinutes",
      "AvgSpeedKm",
      "LastUpdated"
    )
    SELECT
      $3::uuid AS "SurveyId",
      cr."ReportId",
      NULL AS "SurveyorUnit",
      0 AS "SurveyDurationMinutes",
      0 AS "SurveyRawDurationMinutes",
      0 AS "SegmentWeight",
      NULL AS "StartHour",
      NULL AS "StartTime",
      NULL AS "StartEpoch",
      NULL AS "EndTime",
      NULL AS "EndEpoch",
      NULL AS "StartDay",
      NULL AS "EndDay",
      NULL AS "LateralRotation",
      0 AS "NumberOfPeaks",
      0 AS "DaySegments",
      0 AS "NightSegments",
      0 AS "ActiveSegments",
      0 AS "IdleSegments",
      0 AS "TotalSegments",
      0 AS "TotalSegmentsInSurvey",
      0 AS "TotalKilometers",
      0 AS "DayKilometers",
      0 AS "NightKilometers",
      0 AS "IdleTimeMinutes",
      0 AS "ActiveTimeMinutes",
      0 AS "SegmentDurationMinutes",
      0 AS "AvgSpeedKm",
      NOW() AS "LastUpdated"
    FROM %s cr
    WHERE ($1::uuid IS NULL OR cr."CustomerId" = $1)
      AND ($2::uuid IS NULL OR cr."ReportId" = $2)
      AND NOT EXISTS (
        SELECT 1
        FROM %s ss
        WHERE ss."ReportId" = cr."ReportId"
      )
    $sql$,
    target_table,
    report_table,
    target_table
  ) USING p_customer_id, p_report_id, zero_survey_id;
END;
$$;

CREATE OR REPLACE PROCEDURE kpihub.refresh_survey_summary_report(
  p_report_id uuid,
  p_db_location text
)
LANGUAGE plpgsql
AS $$
DECLARE
  report_table text;
  customer_id uuid;
BEGIN
  IF upper(p_db_location) = 'EU2' THEN
    report_table := 'kpihub."MV_ReportSummary_eu2"';
  ELSIF upper(p_db_location) = 'EU1' THEN
    report_table := 'kpihub."MV_ReportSummary_eu1"';
  ELSE
    RAISE EXCEPTION 'Unsupported DB location: % (expected EU1 or EU2)', p_db_location;
  END IF;

  EXECUTE format(
    'SELECT "CustomerId" FROM %s WHERE "ReportId" = $1',
    report_table
  ) INTO customer_id USING p_report_id;

  IF customer_id IS NULL THEN
    RAISE EXCEPTION 'Report % not found in %', p_report_id, report_table;
  END IF;

  CALL kpihub.refresh_survey_summary_customer(customer_id, p_db_location, p_report_id);
END;
$$;

CREATE OR REPLACE PROCEDURE kpihub.refresh_survey_summary()
LANGUAGE plpgsql
AS $$
DECLARE
  cust record;
BEGIN
  SET LOCAL enable_mergejoin = off;

  FOR cust IN
    SELECT customerid, dblocation
    FROM kpihub."KPI_Customer"
    WHERE active IS TRUE
      AND dblocation IS NOT NULL
      AND upper(dblocation) IN ('EU1', 'EU2')
    ORDER BY "Name"
  LOOP
    CALL kpihub.refresh_survey_summary_customer(cust.customerid, cust.dblocation);
  END LOOP;
END;
$$;

CREATE VIEW kpihub."V_SurveySummary" AS
SELECT * FROM kpihub."MV_SurveySummary_eu1"
UNION ALL
SELECT * FROM kpihub."MV_SurveySummary_eu2";

COMMENT ON TABLE kpihub."MV_SurveySummary_eu1" IS
  'EU1 survey summary per (SurveyId, ReportId). Reports without surveys use sentinel SurveyId 00000000-0000-0000-0000-000000000000 with zero metrics.';

COMMENT ON TABLE kpihub."MV_SurveySummary_eu2" IS
  'EU2 survey summary per (SurveyId, ReportId). Reports without surveys use sentinel SurveyId 00000000-0000-0000-0000-000000000000 with zero metrics.';

COMMENT ON PROCEDURE kpihub.refresh_survey_summary() IS
  'Reload survey summaries for active customers in one batched pass per customer. ReportArea from MV_ReportSummary.';
