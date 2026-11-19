CUSTOMER_TABLE = {
    'Name' : 'KPI_Customer',
    'Columns' : {
        'CustomerId': 'uniqueidentifier',
        'Name': 'nvarchar',
        'ShortName': 'nvarchar',
        'Active': 'bit',
        'DBLocation': 'nvarchar',
        'Country': 'nvarchar',
        'LastUpdated': 'datetime',
    },
    'PrimaryKey' : 'CustomerId',
}
#Country Table
COUNTRY_TABLE = {
    'Name' : 'KPI_Country',
    'Columns' : {
        'CountryId': 'uniqueidentifier',
        'Name': 'nvarchar',
        'LastUpdated': 'datetime',
    },
    'PrimaryKey' : 'CountryId',
}

# POR Table
POR_TABLE = {
    'Name' : 'KPI_POR',
    'Columns' : {
        'CustomerId': 'uniqueidentifier',
        'Year': 'int',
        'StartingDate': 'datetime',
        'EndingDate': 'datetime',
        'Description': 'nvarchar',
        'Value': 'float',
        'Unit': 'nvarchar',
        'LastUpdated': 'datetime',
    },
    'PrimaryKey' : ['CustomerId', 'Year'],
}

# Output Excel Locations Table
OUTPUT_EXCEL_LOCATIONS_TABLE = {
    'Name' : 'KPI_OutputExcelLocation',
    'Columns' : {
        'CustomerId': 'uniqueidentifier',
        'BoxFolderId': 'nvarchar',
        'LastUpdated': 'datetime',
    },
    'PrimaryKey' : 'CustomerId',
}

# Utilization Table
UTILIZATION_TABLE = {
    'Name' : 'KPI_Utilization',
    'Columns' : {
        'CustomerId': 'uniqueidentifier',
        'WorkingDays': 'int',
        'WorkingHours': 'int',
        'SunriseHour': 'int',
        'SunsetHour': 'int',
        'BaseSurveyorCount': 'int',
        'Description': 'nvarchar',
        'LastUpdated': 'datetime',
    },
    'PrimaryKey' : 'CustomerId',
}

# Report Summary Table
REPORT_SUMMARY_TABLE = {
    'Name' : 'KPI_ReportSummary',
    'Columns' : {
        'ReportId': 'uniqueidentifier',
        'CustomerId': 'uniqueidentifier',
        'ReportName': 'nvarchar',
        'ReportDate': 'datetime',
        'ReportDateLocal': 'datetime',
        'ReportYear': 'int',
        'ReportMonth': 'int',
        'ReportWeek': 'int',
        'ReportAssetLengthKm': 'float',
        'AssetCoveredLengthKm': 'float',
        'DistributionPipeKm': 'float',
        'DistributionPipeCoveredKm': 'float',
        'ServicePipeKm': 'float',
        'ServicePipeCoveredKm': 'float',
        'BoundaryName': 'nvarchar',
        'BoundaryType': 'nvarchar',
        'BoundaryMode': 'nvarchar',
        'BoundaryPlant': 'nvarchar',
        'BoundarySubplant': 'nvarchar',
        'BoundaryRegion': 'nvarchar',
        'BoundarySubRegion': 'nvarchar',
        'ReportArea': 'geometry',
        'Labels': 'uniqueidentifier',
        'Duplicated': 'nvarchar',
        'TimeZone': 'nvarchar',
        'LastUpdated': 'datetime',
    },
    'PrimaryKey' : 'ReportId',
    'ForeignKey' : 'CustomerId',
}

# Peak SAT Location Table
PEAK_SAT_LOCATION_TABLE = {
    'Name' : 'KPI_PeakSATLocation',
    'Columns' : {
        'CustomerId': 'uniqueidentifier',
        'BoxFileId': 'bigint',
        'LastUpdated': 'datetime',
    },
    'PrimaryKey' : 'CustomerId',
}

# Peak Above SAT Table
PEAK_ABOVE_SAT_TABLE = {
    'Name' : 'KPI_PeakAboveSAT',
    'Columns' : {
        'CustomerId': 'uniqueidentifier',
        'PeakName': 'nvarchar',
        'PeakId': 'uniqueidentifier',
        'Date': 'date',
        'ReportYear': 'int',
        'WeekNumber': 'int',
        'Disposition': 'nvarchar',
        'LocalTime': 'time',
        'BoundaryName': 'nvarchar',
        'BoundaryRegion': 'nvarchar',
        'BoundaryPlant': 'nvarchar',
        'BoundarySubRegion': 'nvarchar',
        'EmissionRate': 'float',
        'PeakGpsLatitude': 'float',
        'PeakGpsLongitude': 'float',
        'Easting': 'float',
        'Northing': 'float',
        'UserName': 'nvarchar',
        'SurveyorUnit': 'nvarchar',
        'AnalyzerSerialNumber': 'nvarchar',
        'Hyperlink': 'nvarchar',
        'LastUpdated': 'datetime',
    },
    'PrimaryKey' : 'PeakId',
    'ForeignKey' : 'CustomerId',
}

# Emission Source Summary Table
EMISSION_SOURCE_SUMMARY_TABLE = {
    'Name' : 'KPI_EmissionSourceSummary',
    'Columns' : {
        'ReportId': 'uniqueidentifier',
        'EmissionRate': 'float',
        'EmissionRateLPM': 'float',
        'RepresentativeEmissionRate': 'float',
        'RepresentativeEmissionRateLPM': 'float',
        'LisaCount': 'int',
        'LisaPSCount': 'int',
        'B0Count': 'int',
        'B1Count': 'int',
        'Bm1Count': 'int',
        'Bm2Count': 'int',
        'B0RepEmissionRateLPM': 'float',
        'B1RepEmissionRateLPM': 'float',
        'Bm1RepEmissionRateLPM': 'float',
        'Bm2RepEmissionRateLPM': 'float',
        'B0RepEmissionRate': 'float',
        'B1RepEmissionRate': 'float',
        'Bm1RepEmissionRate': 'float',
        'Bm2RepEmissionRate': 'float',
        'Not_NGCount': 'int',
        'PGCount': 'int',
        'NGCount': 'int',
        'LastUpdated': 'datetime',
    },
    'PrimaryKey' : 'ReportId',
}

# Survey Summary Table
SURVEY_SUMMARY_TABLE = {
    'Name' : 'KPI_SurveySummary',
    'Columns' : {
        'SurveyId': 'uniqueidentifier',
        'ReportId': 'uniqueidentifier',
        'SurveyorUnit': 'nvarchar',
        'StartDateTimeUTC': 'datetime',
        'StartDateTimeLocal': 'datetime',
        'EndDateTimeUTC': 'datetime',
        'EndDateTimeLocal': 'datetime',
        'StartEpoch': 'bigint',
        'EndEpoch': 'bigint',
        'SurveyDurationMinutes': 'float',
        'SurveyRawDurationMinutes': 'float',
        'SegmentWeight': 'float',
        'LateralRotation': 'nvarchar',
        'NumberOfPeaks': 'int',
        'DaySegments': 'int',
        'NightSegments': 'int',
        'ActiveSegments': 'int',
        'IdleSegments': 'int',
        'TotalSegments': 'int',
        'TotalSegmentsInSurvey': 'int',
        'TotalKilometers': 'float',
        'SurveyTotalKilometers': 'float',
        'DayKilometers': 'float',
        'NightKilometers': 'float',
        'IdleTimeMinutes': 'float',
        'ActiveTimeMinutes': 'float',
        'SegmentDurationMinutes': 'float',
        'AvgSpeedKm': 'float',
        'LastUpdated': 'datetime',
    },
    'PrimaryKey' :['ReportId', 'SurveyId'],
}

# KPI Definition Table
KPI_DEFINITION_TABLE = {
    'Name' : 'KPI_Definition',
    'Columns' : {
        'Name': 'nvarchar',
        'Unit': 'nvarchar',
        'Formula': 'nvarchar',
        'Description': 'nvarchar',
        'Type': 'nvarchar',
        'LastUpdated': 'datetime',
    },
    'PrimaryKey' : 'Name',
}

# KPI Data Table
KPI_DATA_TABLE = {
    'Name' : 'KPI_Data',
    'Columns' : {
        'Id': 'nvarchar',
        'KPIId': 'nvarchar',
        'CustomerId': 'uniqueidentifier',
        'BoundaryRegion': 'nvarchar',
        'BoundaryPlant': 'nvarchar',
        'Year': 'int',
        'PeriodType': 'nvarchar',
        'PeriodValue': 'int',
        'Value': 'nvarchar',
        'DataType': 'nvarchar',
        'LastUpdated': 'datetime',
    },
    'PrimaryKey' : 'Id',
}

TABLE_CONFIG_LIST = [
    CUSTOMER_TABLE,
    COUNTRY_TABLE,
    POR_TABLE,
    KPI_DATA_TABLE,
    OUTPUT_EXCEL_LOCATIONS_TABLE,
    UTILIZATION_TABLE,
    REPORT_SUMMARY_TABLE,
    PEAK_SAT_LOCATION_TABLE,
    PEAK_ABOVE_SAT_TABLE,
    EMISSION_SOURCE_SUMMARY_TABLE,
    SURVEY_SUMMARY_TABLE,
    KPI_DEFINITION_TABLE]