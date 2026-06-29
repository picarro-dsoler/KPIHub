from locallib.picarrodb import *
import sqlite3
from .KPITable import KPITable


# Customer Table
KPI_Customer = KPITable('KPI_Customer')
KPI_Customer.add_column(DBColumn('CustomerId', datatype='uniqueidentifier', key='primary'))
KPI_Customer.add_column(DBColumn('Name', datatype='nvarchar'))
KPI_Customer.add_column(DBColumn('ShortName', datatype='nvarchar'))
KPI_Customer.add_column(DBColumn('DBLocation', datatype='nvarchar'))
KPI_Customer.add_column(DBColumn('LastUpdated', datatype='datetime'))

# POR Table
KPI_POR = KPITable('KPI_PlanOfRecord')
KPI_POR.add_column(DBColumn('Id', datatype='uniqueidentifier', key='primary'))
KPI_POR.add_column(DBColumn('CustomerId', datatype='nvarchar'))
KPI_POR.add_column(DBColumn('StartingDate', datatype='datetime'))
KPI_POR.add_column(DBColumn('EndingDate', datatype='datetime'))
KPI_POR.add_column(DBColumn('Description', datatype='nvarchar'))
KPI_POR.add_column(DBColumn('Value', datatype='float'))
KPI_POR.add_column(DBColumn('LastUpdated', datatype='datetime'))

# ReportDrivingSurvey
KPI_ReportDrivingSurvey = KPITable('KPI_ReportDrivingSurvey')
KPI_ReportDrivingSurvey.add_column(DBColumn('Id', datatype='uniqueidentifier', key='primary'))
KPI_ReportDrivingSurvey.add_column(DBColumn('ReportId', datatype='uniqueidentifier'))
KPI_ReportDrivingSurvey.add_column(DBColumn('SurveyId', datatype='uniqueidentifier'))
KPI_ReportDrivingSurvey.add_column(DBColumn('LastUpdated', datatype='datetime'))

# Utilization Table
KPI_Utilization = KPITable("KPI_Utilization")
KPI_Utilization.add_column(DBColumn('CustomerId', datatype='uniqueidentifier', key='primary'))
KPI_Utilization.add_column(DBColumn('WorkingDays', datatype='int'))
KPI_Utilization.add_column(DBColumn('WorkingHours', datatype='int'))
KPI_Utilization.add_column(DBColumn('BaseSurveyorCount', datatype='int'))
KPI_Utilization.add_column(DBColumn('Description', datatype='nvarchar'))
KPI_Utilization.add_column(DBColumn('LastUpdated', datatype='datetime'))

# Report Summary Table
KPI_ReportSummary = KPITable('KPI_ReportSummary')
KPI_ReportSummary.add_column(DBColumn('ReportId', datatype='uniqueidentifier', key='primary'))
KPI_ReportSummary.add_column(DBColumn('CustomerId', datatype='uniqueidentifier', key='foreign'))
KPI_ReportSummary.add_column(DBColumn('ReportName', datatype='nvarchar'))
KPI_ReportSummary.add_column(DBColumn('ReportDate', datatype='datetime'))
KPI_ReportSummary.add_column(DBColumn('ReportYear', datatype='int'))
KPI_ReportSummary.add_column(DBColumn('ReportMonth', datatype='int'))
KPI_ReportSummary.add_column(DBColumn('ReportWeek', datatype='int'))
KPI_ReportSummary.add_column(DBColumn('ReportAssetLengthKm', datatype='float'))
KPI_ReportSummary.add_column(DBColumn('AssetCoveredLengthKm', datatype='float'))
KPI_ReportSummary.add_column(DBColumn('DistributionPipeKm', datatype='float'))
KPI_ReportSummary.add_column(DBColumn('DistributionPipeCoveredKm', datatype='float'))
KPI_ReportSummary.add_column(DBColumn('ServicePipeKm', datatype='float'))
KPI_ReportSummary.add_column(DBColumn('ServicePipeCoveredKm', datatype='float'))
KPI_ReportSummary.add_column(DBColumn('BoundaryName', datatype='nvarchar'))
KPI_ReportSummary.add_column(DBColumn('BoundaryType', datatype='nvarchar'))
KPI_ReportSummary.add_column(DBColumn('BoundaryMode', datatype='nvarchar'))
KPI_ReportSummary.add_column(DBColumn('BoundaryPlant', datatype='nvarchar'))
KPI_ReportSummary.add_column(DBColumn('BoundarySubplant', datatype='nvarchar'))
KPI_ReportSummary.add_column(DBColumn('BoundaryRegion', datatype='nvarchar'))
KPI_ReportSummary.add_column(DBColumn('BoundarySubRegion', datatype='nvarchar'))
KPI_ReportSummary.add_column(DBColumn('LastUpdated', datatype='datetime'))



# Emission Source Summary Table
KPI_EmissionSourceSummary = KPITable('KPI_EmissionSourceSummary')
KPI_EmissionSourceSummary.add_column(DBColumn('ReportId', datatype='uniqueidentifier', key='primary'))
KPI_EmissionSourceSummary.add_column(DBColumn('EmissionRate', datatype='float'))
KPI_EmissionSourceSummary.add_column(DBColumn('LisaCount', datatype='int'))
KPI_EmissionSourceSummary.add_column(DBColumn('B0Count', datatype='int'))
KPI_EmissionSourceSummary.add_column(DBColumn('B1Count', datatype='int'))
KPI_EmissionSourceSummary.add_column(DBColumn('Bm1Count', datatype='int'))
KPI_EmissionSourceSummary.add_column(DBColumn('Bm2Count', datatype='int'))
KPI_EmissionSourceSummary.add_column(DBColumn('Not_NGCount', datatype='int'))
KPI_EmissionSourceSummary.add_column(DBColumn('PGCount', datatype='int'))
KPI_EmissionSourceSummary.add_column(DBColumn('NGCount', datatype='int'))
KPI_EmissionSourceSummary.add_column(DBColumn('LastUpdated', datatype='datetime'))


# Survey Summary Table
KPI_SurveySummary = KPITable('KPI_SurveySummary')
KPI_SurveySummary.add_column(DBColumn('SurveyId', datatype='uniqueidentifier'))
KPI_SurveySummary.add_column(DBColumn('ReportId', datatype='uniqueidentifier'))
KPI_SurveySummary.add_column(DBColumn('SurveyorUnit', datatype='nvarchar'))
KPI_SurveySummary.add_column(DBColumn('SurveyDurationMinutes', datatype='float'))
KPI_SurveySummary.add_column(DBColumn('StartHour', datatype='int'))
KPI_SurveySummary.add_column(DBColumn('StartTime', datatype='datetime'))
KPI_SurveySummary.add_column(DBColumn('StartEpoch', datatype='bigint'))
KPI_SurveySummary.add_column(DBColumn('EndTime', datatype='datetime'))
KPI_SurveySummary.add_column(DBColumn('EndEpoch', datatype='bigint'))
KPI_SurveySummary.add_column(DBColumn('StartDay', datatype='date'))
KPI_SurveySummary.add_column(DBColumn('EndDay', datatype='date'))
KPI_SurveySummary.add_column(DBColumn('LateralRotation', datatype='nvarchar'))
KPI_SurveySummary.add_column(DBColumn('NumberOfPeaks', datatype='int'))
KPI_SurveySummary.add_column(DBColumn('DaySegments', datatype='int'))
KPI_SurveySummary.add_column(DBColumn('NightSegments', datatype='int'))
KPI_SurveySummary.add_column(DBColumn('ActiveSegments', datatype='int'))
KPI_SurveySummary.add_column(DBColumn('IdleSegments', datatype='int'))
KPI_SurveySummary.add_column(DBColumn('TotalSegments', datatype='int'))
KPI_SurveySummary.add_column(DBColumn('TotalKilometers', datatype='float'))
KPI_SurveySummary.add_column(DBColumn('DayKilometers', datatype='float'))
KPI_SurveySummary.add_column(DBColumn('NightKilometers', datatype='float'))
KPI_SurveySummary.add_column(DBColumn('SegmentDurationMinutes', datatype='float'))
KPI_SurveySummary.add_column(DBColumn('IdleTimeMinutes', datatype='float'))
KPI_SurveySummary.add_column(DBColumn('ActiveTimeMinutes', datatype='float'))
KPI_SurveySummary.add_column(DBColumn('AvgSpeedKm', datatype='float'))
KPI_SurveySummary.add_column(DBColumn('LastUpdated', datatype='datetime'))

#Leak Summary Table

#KPI Table
KPI_Definition = KPITable('KPI_Definition')
KPI_Definition.add_column(DBColumn('Name', datatype='nvarchar', key='primary'))
KPI_Definition.add_column(DBColumn('Unit', datatype='nvarchar'))
KPI_Definition.add_column(DBColumn('Formula', datatype='nvarchar'))
KPI_Definition.add_column(DBColumn('Description', datatype='nvarchar'))
KPI_Definition.add_column(DBColumn('LastUpdated', datatype='datetime'))

#KPI_Data Table
KPI_Data = KPITable('KPI_Data')
KPI_Data.add_column(DBColumn('Id', datatype='nvarchar', key='primary'))
KPI_Data.add_column(DBColumn('KPIId', datatype='nvarchar'))
KPI_Data.add_column(DBColumn('CustomerId', datatype='uniqueidentifier'))
KPI_Data.add_column(DBColumn('BoundaryRegion', datatype='nvarchar'))
KPI_Data.add_column(DBColumn('Year', datatype='int'))
KPI_Data.add_column(DBColumn('PeriodType', datatype='int'))
KPI_Data.add_column(DBColumn('PeriodValue', datatype='int'))
KPI_Data.add_column(DBColumn('Value', datatype='nvarchar'))
KPI_Data.add_column(DBColumn('DataType', datatype='nvarchar'))
KPI_Data.add_column(DBColumn('LastUpdated', datatype='datetime'))

#KPI_RegionalData Table
KPI_RegionalData = KPITable('KPI_RegionalData')
KPI_RegionalData.add_column(DBColumn('Id', datatype='nvarchar', key='primary'))
KPI_RegionalData.add_column(DBColumn('KPIId', datatype='nvarchar'))
KPI_RegionalData.add_column(DBColumn('CustomerId', datatype='uniqueidentifier'))
KPI_RegionalData.add_column(DBColumn('Region', datatype='nvarchar'))
KPI_RegionalData.add_column(DBColumn('Year', datatype='int'))
KPI_RegionalData.add_column(DBColumn('PeriodType', datatype='int'))
KPI_RegionalData.add_column(DBColumn('PeriodValue', datatype='int'))
KPI_RegionalData.add_column(DBColumn('Value', datatype='nvarchar'))
KPI_RegionalData.add_column(DBColumn('DataType', datatype='nvarchar'))
KPI_RegionalData.add_column(DBColumn('LastUpdated', datatype='datetime'))
