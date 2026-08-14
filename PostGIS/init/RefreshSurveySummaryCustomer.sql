-- Refresh survey summary for one customer (loops one report at a time).
--
-- Option A: Python ingester (recommended; uses SurveySummaryIngester logic + LSDB):
--   cd /home/dsoler/david-repos/KPIHub
--   PYTHONPATH="../packages:.:lib" python3 PostGIS/init/RefreshSurveySummary.py \
--     --customer-name 'Avacon'
--
-- Option B: SQL procedure (may OOM on large geometry over tds_fdw):
--   psql -h localhost -U dsoler -d Datanalytics -v ON_ERROR_STOP=1 \
--     -f /home/dsoler/david-repos/KPIHub/PostGIS/init/RefreshSurveySummaryCustomer.sql
--
--   psql -h localhost -U dsoler -d Datanalytics -v ON_ERROR_STOP=1 \
--     -v customer_id='93a15fc7-dcb8-4be9-1224-3a1f698b9c1f' \
--     -v db_location='EU1' \
--     -f /home/dsoler/david-repos/KPIHub/PostGIS/init/RefreshSurveySummaryCustomer.sql
--
-- List active customers:
--   SELECT customerid, "Name", dblocation
--   FROM kpihub."KPI_Customer"
--   WHERE active IS TRUE
--   ORDER BY "Name";

\set ON_ERROR_STOP on

-- Default: smallest EU1 customer by report count (override with -v customer_id=...)
\if :{?customer_id}
\else
\set customer_id '93a15fc7-dcb8-4be9-1224-3a1f698b9c1f'
\endif

\if :{?db_location}
\else
\set db_location 'EU1'
\endif

\echo 'Customer:'
SELECT customerid, "Name", dblocation
FROM kpihub."KPI_Customer"
WHERE customerid = :'customer_id'::uuid;

\echo 'Reports for customer:'
SELECT COUNT(*) AS report_count
FROM kpihub."MV_ReportSummary_eu1"
WHERE "CustomerId" = :'customer_id'::uuid
UNION ALL
SELECT COUNT(*)
FROM kpihub."MV_ReportSummary_eu2"
WHERE "CustomerId" = :'customer_id'::uuid;

\echo 'Refreshing survey summary...'
CALL kpihub.refresh_survey_summary_customer(
  :'customer_id'::uuid,
  :'db_location'
);

\echo 'Result:'
SELECT COUNT(*) AS survey_rows
FROM kpihub."V_SurveySummary" ss
JOIN kpihub."MV_ReportSummary_eu1" r ON r."ReportId" = ss."ReportId"
WHERE r."CustomerId" = :'customer_id'::uuid
UNION ALL
SELECT COUNT(*)
FROM kpihub."V_SurveySummary" ss
JOIN kpihub."MV_ReportSummary_eu2" r ON r."ReportId" = ss."ReportId"
WHERE r."CustomerId" = :'customer_id'::uuid;
