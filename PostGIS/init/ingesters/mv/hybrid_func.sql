-- EU2 hybrid refresh: eu2_tds (tabular) + eu2_geo (ReportArea geometry).
-- Prerequisite: KPIHub/PostGIS/DBInit/migrate_eu2_hybrid_fdw.sql

DROP FUNCTION IF EXISTS kpihub.refresh_mv_kpireportsummary_eu2();

CREATE OR REPLACE FUNCTION kpihub.refresh_mv_kpireportsummary_eu2()
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
AS $$
#variable_conflict use_column
DECLARE
    last_mv_report_date timestamp;
    report_ids_count integer;
    report_id_sql text;
BEGIN
    -- SELECT COALESCE(MAX(mv."ReportDate"), '2023-01-01'::timestamp)
    SELECT '2026-08-18 00:00:00'::timestamp
    INTO last_mv_report_date
    FROM kpihub."MV_KPIReportSummary_eu2" mv;

    -- Step 1: discover new report IDs via tds_fdw (DateStarted pushdown to MSSQL).
    DROP TABLE IF EXISTS tmp_new_report_ids;
    EXECUTE format(
        'CREATE TEMP TABLE tmp_new_report_ids ON COMMIT DROP AS
        SELECT R."Id"::uuid AS "ReportId"
        FROM eu2_tds."Report" R
        INNER JOIN eu2_tds."ReportLabel" RL ON R."Id" = RL."ReportId"
        INNER JOIN eu2_tds."Label" L ON RL."LabelId" = L."Id"
        WHERE L."Title" = ''Final Checkbox''
          AND RL."IsActive" = 1
          AND R."DateStarted" > %L::timestamp',
        last_mv_report_date
    );

    SELECT COUNT(*) INTO report_ids_count FROM tmp_new_report_ids;

    IF report_ids_count = 0 THEN
        RETURN;
    END IF;

    -- Step 2: fetch geometry only for known IDs via ogr_fdw (literal IN list).
    SELECT string_agg(quote_literal("ReportId"::text), ',')
    INTO report_id_sql
    FROM tmp_new_report_ids;

    DROP TABLE IF EXISTS tmp_report_areas;
    EXECUTE format(
        'CREATE TEMP TABLE tmp_report_areas ON COMMIT DROP AS
        SELECT RA."ReportId"::uuid AS "ReportId", RA."Shape" AS "ReportArea"
        FROM eu2_geo."ReportArea" RA
        WHERE RA."ReportId"::uuid IN (%s)',
        report_id_sql
    );

    -- Step 3: assemble row from local ID list + tds tabular + local geometry cache.
    RETURN QUERY
    SELECT
        R."Id"::uuid AS "ReportId",
        C."Id"::uuid AS "CustomerId",
        CASE
            WHEN RT."Description" = 'Compliance' THEN 'CR-' || SUBSTRING(R."Id"::text, 1, 6)
            WHEN RT."Description" = 'Emissions' THEN 'ER-' || SUBSTRING(R."Id"::text, 1, 6)
            ELSE 'CR-' || SUBSTRING(R."Id"::text, 1, 6)
        END::text AS "ReportName",
        (R."DateStarted" AT TIME ZONE 'UTC')::timestamp AS "ReportDate",
        EXTRACT(YEAR FROM (R."DateStarted" AT TIME ZONE 'UTC'))::int AS "ReportYear",
        EXTRACT(MONTH FROM (R."DateStarted" AT TIME ZONE 'UTC'))::int AS "ReportMonth",
        EXTRACT(WEEK FROM (R."DateStarted" AT TIME ZONE 'UTC'))::int AS "ReportWeek",
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
        RA."ReportArea",
        (NOW() AT TIME ZONE 'UTC')::timestamp AS "LastUpdated"
    FROM tmp_new_report_ids NR
    INNER JOIN eu2_tds."Report" R ON NR."ReportId" = R."Id"::uuid
    INNER JOIN eu2_tds."Customer" C ON R."CustomerId" = C."Id"::uuid
    INNER JOIN eu2_tds."ReportLabel" RL ON R."Id" = RL."ReportId"
    INNER JOIN eu2_tds."Label" L ON RL."LabelId" = L."Id"
    LEFT JOIN eu2_tds."ReportType" RT ON R."ReportTypeId" = RT."Id"
    LEFT JOIN eu2_tds."ReportCompliance" RC ON R."Id" = RC."ReportId"
    LEFT JOIN eu2_tds."ReportAreaCovered" RAC ON R."Id" = RAC."ReportId"
    LEFT JOIN tmp_report_areas RA ON NR."ReportId" = RA."ReportId"
    LEFT JOIN dash.v_report dh ON dh.rp_id = R."Id"::uuid
    WHERE L."Title" = 'Final Checkbox'
      AND RL."IsActive" = 1;

    RETURN;
END;
$$;

COMMENT ON FUNCTION kpihub.refresh_mv_kpireportsummary_eu2() IS
  'EU2 incremental report rows: IDs via eu2_tds (tds_fdw), ReportArea via eu2_geo (ogr_fdw).';

-- Preview new rows:
SELECT * FROM kpihub.refresh_mv_kpireportsummary_eu2();
--
-- Insert into MV:
-- INSERT INTO kpihub."MV_KPIReportSummary_eu2"
-- SELECT * FROM kpihub.refresh_mv_kpireportsummary_eu2();
