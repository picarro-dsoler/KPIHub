from locallib.picarrodb import *

ReportSummaryTable = DBTable('ReportSummaryTable')
ReportSummaryTable.add_column(DBColumn('ReportId', datatype='uniqueidentifier'))
ReportSummaryTable.add_column(DBColumn('ReportName', datatype='nvarchar'))
ReportSummaryTable.add_column(DBColumn('ReportDate', datatype='datetime'))
ReportSummaryTable.add_column(DBColumn('ReportAssetLengthKm', datatype='float'))
ReportSummaryTable.add_column(DBColumn('AssetCoveredLengthKm', datatype='float'))
ReportSummaryTable.add_column(DBColumn('DistributionPipeKm', datatype='float'))
ReportSummaryTable.add_column(DBColumn('DistributionPipeCoveredKm', datatype='float'))
ReportSummaryTable.add_column(DBColumn('ServicePipeKm', datatype='float'))
ReportSummaryTable.add_column(DBColumn('ServicePipeCoveredKm', datatype='float'))
ReportSummaryTable.add_column(DBColumn('LastUpdated', datatype='datetime'))
