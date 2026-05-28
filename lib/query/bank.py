from locallib.query.Query import Query
from locallib.picarrodb import *

def setup_query(query_func):
    def wrapper(*args, **kwargs):
        query = query_func(*args, **kwargs)
        return Query(query = query)
    return wrapper


@setup_query
def get_reports(customer_name, table_name = None, years=None, final_checkbox = True):
    year_filter = ""
    if years:
        years_str = ", ".join(str(year) for year in years)
        year_filter = f"AND YEAR(R.DateStarted) IN ({years_str})"

    if table_name is not None:
        into_clause = f"INTO {table_name}"
    else:
        into_clause = ""

    if final_checkbox:
        label_filter = "AND L.Title = 'Final Checkbox'"
    else:
        label_filter = ""

    query = f"""
    SELECT 
        C.Name AS CustomerName,
        CASE
            WHEN ReportType.Description = 'Compliance' THEN CONCAT('CR-', SUBSTRING(CONVERT(nvarchar(50), R.Id), 1, 6))
            WHEN ReportType.Description = 'Emissions' THEN CONCAT('ER-', SUBSTRING(CONVERT(nvarchar(50), R.Id), 1, 6))
            ELSE CONCAT('CR-', SUBSTRING(CONVERT(nvarchar(50), R.Id), 1, 6))
        END AS ReportName,
        R.Id AS ReportId,
        R.ReportTitle AS ReportTitle,
        L.Title AS Label,
        R.DateStarted AS ReportDate,
        RA.ExternalId AS BoundaryName,
        RA.BoundaryType AS BoundaryType,
        RAC.AssetLengthKM AS ReportAssetLengthKm,
        RC.PercentCoverageAssets AS ReportPercentCoverageAssets,
        RAC.AssetLengthKM * RC.PercentCoverageAssets AS AssetCoveredLengthKm,
        RAC.DistributionPipeKm,
        RAC.DistributionPipeCoveredKm,
        RAC.DistributionPipePercentCovered,
        RAC.ServicePipeKm,
        RAC.ServicePipeCoveredKm,
        YEAR(R.DateStarted) AS ReportYear,
        MONTH(R.DateStarted) AS ReportMonth,
        DATEPART(WEEK, R.DateStarted) AS ReportWeek,
        DATEPART(QUARTER, R.DateStarted) AS ReportQuarter
    {into_clause}
    FROM
        Report R
    LEFT JOIN Customer C ON
        R.CustomerId = C.Id
    LEFT JOIN ReportLabel RL ON
        R.Id = RL.ReportId
    LEFT JOIN Label L ON
        RL.LabelId = L.Id
    LEFT JOIN ReportType ON
        R.ReportTypeId = ReportType.Id
    LEFT JOIN ReportArea RA ON R.Id = RA.ReportId
    LEFT JOIN ReportCompliance RC ON R.Id = RC.ReportId
    LEFT JOIN ReportAreaCovered RAC ON R.Id = RAC.ReportId
    WHERE
        LOWER(C.Name) = LOWER('{customer_name}')
        AND L.Title = 'Final Checkbox'
        AND RL.IsActive = 1
        {year_filter}
    """
    return query

@setup_query
def query_reports_view(report_table,table_name = None):
    if table_name is not None:
        into_clause = f"INTO {table_name}"
    else:
        into_clause = ""
    query = f"""SELECT 
    rp_id AS "ReportId",
    rp_label_other AS "ReportLabelOther",
    bo_name AS "BoundaryName",
    bo_mode AS "BoundaryMode",
    bo_type AS "BoundaryType",
    bo_plant AS "BoundaryPlant",
    bo_subplant AS "BoundarySubplant",
    bo_region AS "BoundaryRegion",
    bo_subregion AS "BoundarySubRegion",
    bo_km_network AS "BoundaryKmNetwork"
    {into_clause}
    from dash.v_report 
    where rp_id IN (SELECT LOWER(ReportId::text)::uuid FROM {report_table})"""
    return query
