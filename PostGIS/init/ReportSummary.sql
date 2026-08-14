SET enable_mergejoin = off;

DROP MATERIALIZED VIEW IF EXISTS kpihub."MV_ReportSummary_eu1";
DROP MATERIALIZED VIEW IF EXISTS kpihub."MV_ReportSummary_eu2";
DROP VIEW IF EXISTS kpihub."MV_ReportSummary_eu1";
DROP VIEW IF EXISTS kpihub."MV_ReportSummary_eu2";
DROP MATERIALIZED VIEW IF EXISTS kpihub."MV_ReportSummary";
DROP VIEW IF EXISTS kpihub."V_ReportSummary";

DROP TABLE IF EXISTS kpihub."MV_ReportSummary_eu1";
DROP TABLE IF EXISTS kpihub."MV_ReportSummary_eu2";
DROP TABLE IF EXISTS kpihub."ReportAreaCache_eu1";
DROP TABLE IF EXISTS kpihub."ReportAreaCache_eu2";

-- EU1 materialized view
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
  NULL::text AS "ReportArea",
  NOW() AS "LastUpdated"
FROM eu1."Report" R
INNER JOIN eu1."Customer" C ON R."CustomerId" = C."Id"
LEFT JOIN eu1."ReportLabel" RL ON R."Id" = RL."ReportId"
LEFT JOIN eu1."Label" L ON RL."LabelId" = L."Id"
LEFT JOIN eu1."ReportType" RT ON R."ReportTypeId" = RT."Id"
LEFT JOIN eu1."ReportCompliance" RC ON R."Id" = RC."ReportId"
LEFT JOIN eu1."ReportAreaCovered" RAC ON R."Id" = RAC."ReportId"
LEFT JOIN dash.v_report dh ON dh.rp_id = R."Id"
WHERE L."Title" = 'Final Checkbox'
  AND RL."IsActive" = 1
  AND R."DateStarted" >= DATE '2023-01-01'
  AND C."Id" IN (
    SELECT kc2.customerid
    FROM kpihub."KPI_Customer" kc2
    WHERE kc2.active IS TRUE
      AND kc2.dblocation IS NOT NULL
      AND upper(kc2.dblocation) = 'EU1'
  )
WITH NO DATA;

-- EU2 materialized view
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
  NULL::text AS "ReportArea",
  NOW() AS "LastUpdated"
FROM eu2."Report" R
INNER JOIN eu2."Customer" C ON R."CustomerId" = C."Id"
LEFT JOIN eu2."ReportLabel" RL ON R."Id" = RL."ReportId"
LEFT JOIN eu2."Label" L ON RL."LabelId" = L."Id"
LEFT JOIN eu2."ReportType" RT ON R."ReportTypeId" = RT."Id"
LEFT JOIN eu2."ReportCompliance" RC ON R."Id" = RC."ReportId"
LEFT JOIN eu2."ReportAreaCovered" RAC ON R."Id" = RAC."ReportId"
LEFT JOIN dash.v_report dh ON dh.rp_id = R."Id"
WHERE L."Title" = 'Final Checkbox'
  AND RL."IsActive" = 1
  AND R."DateStarted" >= DATE '2023-01-01'
  AND C."Id" IN (
    SELECT kc2.customerid
    FROM kpihub."KPI_Customer" kc2
    WHERE kc2.active IS TRUE
      AND kc2.dblocation IS NOT NULL
      AND upper(kc2.dblocation) = 'EU2'
  )
WITH NO DATA;

CREATE TABLE kpihub."ReportAreaCache_eu1" (
  "ReportId" uuid PRIMARY KEY,
  "ReportArea" text
);

CREATE TABLE kpihub."ReportAreaCache_eu2" (
  LIKE kpihub."ReportAreaCache_eu1" INCLUDING ALL
);

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
  'EU1 report summary snapshot for active KPI_Customer rows. Refresh via REFRESH MATERIALIZED VIEW kpihub."MV_ReportSummary_eu1".';

COMMENT ON MATERIALIZED VIEW kpihub."MV_ReportSummary_eu2" IS
  'EU2 report summary snapshot for active KPI_Customer rows. Refresh via REFRESH MATERIALIZED VIEW kpihub."MV_ReportSummary_eu2".';