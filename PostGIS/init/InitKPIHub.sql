-- KPIHub PostGIS full init (run this one file from anywhere)
--
-- From shell:
--   psql -h localhost -U dsoler -d Datanalytics -v ON_ERROR_STOP=1 \
--     -f /home/dsoler/david-repos/KPIHub/PostGIS/init/InitKPIHub.sql
--
-- From psql:
--   \i /home/dsoler/david-repos/KPIHub/PostGIS/init/InitKPIHub.sql
--
-- Uses \ir so included files resolve relative to this script's directory.

\echo '==> IngesterTables.sql'
\ir IngesterTables.sql

\echo '==> SeedCustomerInfo.sql'
\ir SeedCustomerInfo.sql

\echo '==> ReportSummaryMaterializedView.sql'
\ir ReportSummaryMaterializedView.sql

\echo '==> refresh_report_summary()'
CALL kpihub.refresh_report_summary();

\echo '==> EmissionSourceSummaryMaterializedView.sql'
\ir EmissionSourceSummaryMaterializedView.sql

\echo '==> refresh_emission_source_summary()'
CALL kpihub.refresh_emission_source_summary();

\echo '==> SurveySummaryMaterializedView.sql'
\ir SurveySummaryMaterializedView.sql

-- Survey refresh pulls Segment.Shape over tds_fdw per report and can OOM Postgres in Docker.
-- Run manually when needed (optionally after: CALL kpihub.refresh_report_areas();):
--   CALL kpihub.refresh_survey_summary();
-- \echo '==> refresh_survey_summary()'
-- CALL kpihub.refresh_survey_summary();

\echo '==> Done'
SELECT
  (SELECT COUNT(*) FROM kpihub."KPI_Customer" WHERE active IS TRUE) AS active_customers,
  (SELECT COUNT(*) FROM kpihub."V_ReportSummary") AS report_rows,
  (SELECT COUNT(*) FROM kpihub."V_EmissionSourceSummary") AS emission_rows,
  (SELECT COUNT(*) FROM kpihub."V_SurveySummary") AS survey_rows;
