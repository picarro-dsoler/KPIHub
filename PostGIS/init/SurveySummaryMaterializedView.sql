-- Survey summary snapshot tables mirroring lib/ingester/SurveySummaryIngester.py
--
-- These are regular TABLES (not PostgreSQL materialized views). Query them via:
--   \dt kpihub."MV_SurveySummary_*"
--   SELECT * FROM kpihub."V_SurveySummary";
--
-- When ReportArea exists for a report, segments are filtered by ST_Intersects.
-- ReportArea is fetched per report from eu1/eu2."ReportArea" (foreign table), not
-- from MV_ReportSummary. When no area is found, all survey segments are used.
--
-- Config mirrors lib/config.py: SUNRISE_TIME=6, SUNSET_TIME=20, SPEED_THRESHOLD=0.5
--
-- Prerequisite:
--   1. IngesterTables.sql, SeedCustomerInfo.sql
--   2. ReportSummaryMaterializedView.sql + CALL kpihub.refresh_report_summary();
--
-- Setup:
--   psql -U dsoler -d Datanalytics -v ON_ERROR_STOP=1 -f SurveySummaryMaterializedView.sql
--
-- Load / refresh (loops per report within each customer):
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

CREATE OR REPLACE PROCEDURE kpihub.refresh_survey_summary_report(
  p_report_id uuid,
  p_db_location text
)
LANGUAGE plpgsql
AS $$
DECLARE
  lsdb_schema text;
  target_table text;
  report_geom geometry;
BEGIN
  IF upper(p_db_location) = 'EU2' THEN
    lsdb_schema := 'eu2';
    target_table := 'kpihub."MV_SurveySummary_eu2"';
  ELSIF upper(p_db_location) = 'EU1' THEN
    lsdb_schema := 'eu1';
    target_table := 'kpihub."MV_SurveySummary_eu1"';
  ELSE
    RAISE EXCEPTION 'Unsupported DB location: % (expected EU1 or EU2)', p_db_location;
  END IF;

  report_geom := NULL;
  BEGIN
    EXECUTE format(
      $sql$
      SELECT ST_GeomFromText(RA."Shape", 4326)
      FROM %I."ReportArea" RA
      WHERE RA."ReportId" = $1
        AND RA."Shape" IS NOT NULL
        AND btrim(RA."Shape") <> ''
      LIMIT 1
      $sql$,
      lsdb_schema
    ) INTO report_geom USING p_report_id;
  EXCEPTION
    WHEN OTHERS THEN
      RAISE NOTICE 'Report %: could not load ReportArea from %, using all segments. %',
        p_report_id, lsdb_schema, SQLERRM;
      report_geom := NULL;
  END;

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
    WITH report_area AS (
      SELECT $2::geometry AS geom
      WHERE $2 IS NOT NULL
    ),
    report_surveys AS (
      SELECT
        S."Id" AS "SurveyId",
        RDS."ReportId",
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
      FROM %I."Survey" S
      INNER JOIN %I."ReportDrivingSurvey" RDS ON S."Id" = RDS."SurveyId"
      LEFT JOIN %I."SurveyQACheck" SQC ON S."Id" = SQC."SurveyId"
      LEFT JOIN %I."SurveyorUnit" SU ON S."SurveyorUnitId" = SU."Id"
      WHERE RDS."ReportId" = $1
    ),
    survey_segment_counts AS (
      SELECT
        seg."SurveyId",
        COUNT(*)::int AS "TotalSegmentsInSurvey"
      FROM %I."Segment" seg
      INNER JOIN report_surveys rs ON seg."SurveyId" = rs."SurveyId"
      GROUP BY seg."SurveyId"
    ),
    surveys AS (
      SELECT
        rs.*,
        COALESCE(ssc."TotalSegmentsInSurvey", 0) AS "TotalSegmentsInSurvey"
      FROM report_surveys rs
      LEFT JOIN survey_segment_counts ssc ON rs."SurveyId" = ssc."SurveyId"
    ),
    segments_filtered AS (
      SELECT
        seg."SurveyId",
        seg."LengthMeters",
        seg."DurationSeconds",
        seg."CarSpeedMedian",
        CASE
          WHEN EXTRACT(HOUR FROM to_timestamp(seg."StartEpoch")) >= 6
           AND EXTRACT(HOUR FROM to_timestamp(seg."StartEpoch")) < 20
          THEN 'Day'
          ELSE 'Night'
        END AS day_night,
        CASE
          WHEN COALESCE(seg."CarSpeedMedian", 0) < 0.5 THEN 'Idle'
          ELSE 'Active'
        END AS active_idle
      FROM %I."Segment" seg
      INNER JOIN surveys s ON seg."SurveyId" = s."SurveyId"
      WHERE (
        NOT EXISTS (SELECT 1 FROM report_area)
        OR (
          seg."Shape" IS NOT NULL
          AND btrim(seg."Shape") <> ''
          AND EXISTS (
            SELECT 1
            FROM report_area ra
            WHERE ST_Intersects(ST_GeomFromText(seg."Shape", 4326), ra.geom)
          )
        )
      )
    ),
    segment_agg AS (
      SELECT
        "SurveyId",
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
      GROUP BY "SurveyId"
    )
    SELECT
      s."SurveyId",
      s."ReportId",
      s."SurveyorUnit",
      s."SurveyRawDurationMinutes"
        * (sa."TotalSegments"::double precision / NULLIF(s."TotalSegmentsInSurvey", 0))
        AS "SurveyDurationMinutes",
      s."SurveyRawDurationMinutes",
      sa."TotalSegments"::double precision / NULLIF(s."TotalSegmentsInSurvey", 0) AS "SegmentWeight",
      s."StartHour",
      s."StartTime",
      s."StartEpoch",
      s."EndTime",
      s."EndEpoch",
      s."StartDay",
      s."EndDay",
      s."LateralRotation",
      s."NumberOfPeaks",
      sa."DaySegments",
      sa."NightSegments",
      sa."ActiveSegments",
      sa."IdleSegments",
      sa."TotalSegments",
      s."TotalSegmentsInSurvey",
      sa."TotalKilometers",
      sa."DayKilometers",
      sa."NightKilometers",
      sa."IdleTimeMinutes",
      sa."ActiveTimeMinutes",
      sa."SegmentDurationMinutes",
      sa."AvgSpeedKm",
      NOW() AS "LastUpdated"
    FROM surveys s
    INNER JOIN segment_agg sa ON s."SurveyId" = sa."SurveyId"
    $sql$,
    target_table,
    lsdb_schema,
    lsdb_schema,
    lsdb_schema,
    lsdb_schema,
    lsdb_schema,
    lsdb_schema
  ) USING p_report_id, report_geom;
END;
$$;

CREATE OR REPLACE PROCEDURE kpihub.refresh_survey_summary_customer(
  p_customer_id uuid,
  p_db_location text
)
LANGUAGE plpgsql
AS $$
DECLARE
  report_table text;
  target_table text;
  rep record;
BEGIN
  IF upper(p_db_location) = 'EU2' THEN
    report_table := 'kpihub."MV_ReportSummary_eu2"';
    target_table := 'kpihub."MV_SurveySummary_eu2"';
  ELSIF upper(p_db_location) = 'EU1' THEN
    report_table := 'kpihub."MV_ReportSummary_eu1"';
    target_table := 'kpihub."MV_SurveySummary_eu1"';
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

  FOR rep IN
    EXECUTE format(
      'SELECT "ReportId" FROM %s WHERE "CustomerId" = $1 ORDER BY "ReportDate"',
      report_table
    )
    USING p_customer_id
  LOOP
    CALL kpihub.refresh_survey_summary_report(rep."ReportId", p_db_location);
  END LOOP;
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
  'EU1 survey summary per (SurveyId, ReportId) with report-area segment filtering.';

COMMENT ON TABLE kpihub."MV_SurveySummary_eu2" IS
  'EU2 survey summary per (SurveyId, ReportId) with report-area segment filtering.';

COMMENT ON PROCEDURE kpihub.refresh_survey_summary() IS
  'Reload survey summaries for active customers. ReportArea is fetched per report from eu1/eu2 foreign tables.';
