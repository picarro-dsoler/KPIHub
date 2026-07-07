from locallib.query.Query import Query
from locallib.picarrodb import *

def setup_query(query_func):
    def wrapper(*args, **kwargs):
        query = query_func(*args, **kwargs)
        return Query(query = query)
    return wrapper


@setup_query
def get_reports(customer_name, table_name = None, starting_date=None, final_checkbox = True):
    date_filter = ""
    if starting_date:
        date_filter = f"AND R.DateStarted >= '{starting_date}'"
 
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
        C.Id AS CustomerId,
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
        RAC.ServicePipeCoveredKm
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
        {date_filter}
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

@setup_query
def query_emission_sources_table(report_table = None, table_name = None):
    ES_Columns = EmissionSource.copy()
    ES_Columns.delete_column('Lisa')
    ES_Columns.set_column_alias('Id','EmissionSourceId')

    if table_name is not None:
        into_clause = f"INTO {table_name}"
    else:
        into_clause = ""
    query = f"""SELECT {ES_Columns.get_columns()} {into_clause} FROM EmissionSource ES WHERE ES.ReportId IN (SELECT ReportId FROM {report_table})"""
    return query

@setup_query
def query_surveys_table(report_table = None, table_name = None):
    Survey_Columns = Survey.copy()
    Survey_Columns.delete_column('SurveyAreaBoundary')
    Survey_Columns.set_column_alias('Id','SurveyId')
    if table_name is not None:
        into_clause = f"INTO {table_name}"
    else:
        into_clause = ""
    query = f"""SELECT {Survey_Columns.get_columns()},
    SQC.LateralRotation as LateralRotation,
    SQC.NumberOfPeaks as NumberOfPeaks,
    (SELECT Description FROM SurveyorUnit SU WHERE SU.Id = S.SurveyorUnitId) AS SurveyorUnit,
    RDS.ReportId AS ReportId 
    {into_clause} FROM Survey S 
    LEFT JOIN ReportDrivingSurvey RDS ON S.Id = RDS.SurveyId
    LEFT JOIN SurveyQACheck SQC ON S.Id = SQC.SurveyId
    WHERE RDS.ReportId IN (SELECT ReportId FROM {report_table})"""
    return query


@setup_query
def query_segments_table(survey_table = None, table_name = None):
    segments_Columns = Segment.copy()
    #segments_Columns.delete_column('Shape')
    segments_Columns.delete_column('Order')
    if table_name is not None:
        into_clause = f"INTO {table_name}"
    else:
        into_clause = ""
    query = f"""SELECT {segments_Columns.get_columns()}, S.[Order] as [Order] {into_clause} FROM Segment S WHERE S.SurveyId IN (SELECT SurveyId FROM {survey_table}) """
    return query

