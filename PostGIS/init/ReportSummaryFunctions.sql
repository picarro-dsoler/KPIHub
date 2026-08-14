-- Optional helpers for report summary snapshots.
-- Main setup and refresh live in ReportSummaryMaterializedView.sql.
--
-- Usage:
--   psql -U dsoler -d Datanalytics -v ON_ERROR_STOP=1 -f ReportSummaryFunctions.sql
--
-- Refresh one customer:
--   CALL kpihub.refresh_report_summary_customer(
--     'c6565aaf-5251-1dbe-8d39-3a1f45b580a9',
--     'EU1'
--   );
--
-- Refresh all active customers:
--   CALL kpihub.refresh_report_summary();

\echo 'Report summary refresh procedures are defined in ReportSummaryMaterializedView.sql'
