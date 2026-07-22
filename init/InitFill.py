import os
import sys
import pandas as pd

directory = os.path.abspath(os.path.dirname(__file__))
_root = os.path.abspath(os.path.join(directory, ".."))

# Add KPIHub root to sys.path so `lib.*` imports resolve regardless of cwd.
sys.path.insert(0, _root)
os.chdir(_root)

import sqlite3


from locallib.picarrodb import *
from locallib.query import *

from lib.tables.IngesterTables import *
from lib.handlers.CustomerHandler import *
from lib.config import *
from lib.KPIHubConnection import *

#Add customer
add_customer('ITALGAS',EU2_Conn)
add_customer('Westnetz',EU1_Conn)

#Add KP Utilization
add_customer_utilization('ITALGAS', 6, 5, 2, KPIHub_Conn)
add_customer_utilization('Westnetz', 6, 5, 2, KPIHub_Conn)

#Add KPI Output Excel Location
add_output_excel_location('ITALGAS', 401896871043, KPIHub_Conn)
add_output_excel_location('Westnetz', 398249270000, KPIHub_Conn)
#Add KPI POR
add_por(
    customer_name = 'ITALGAS',
    year = 2026,
    value = 0,
    StartingDate = '01-01-2026',
    EndingDate = '31-12-2026',
    Description = ''
)
add_por(
    customer_name = 'Westnetz',
    year = 2026,
    value = 0,
    StartingDate = '01-01-2026',
    EndingDate = '31-12-2026',
    Description = ''
)
#Add KPI Definition
output_dict={
    'PeriodValue': ['', 'Number of the week starting from 1st of Jan', ''],
    'ReportAssetLengthKm': ['Km', 'Total length of all the assets in the specified period', ''],
    'AssetCoveredLengthKm': ['Km', 'Total length of all the assets covered in the report', ''],
    'CumulativeAssetCoveredLengthKm': ['Km', 'Cumulative covered length of all the assets covered in the indicated period', ''],
    'DistributionPipeKm': ['Km', 'Total length of all the mains in the report', ''],
    'DistributionPipeCoveredKm': ['Km', 'Total length of all the mains covered in the report', ''],
    'ServicePipeKm': ['Km', 'Total length of all the services in the report', ''],
    'ServicePipeCoveredKm': ['Km', 'Total length of all the services covered in the report', ''],
    'ReportCount': ['Report', 'Total number of reports in the specified week', ''],
    'DaysCount': ['Day', 'Total number of days worked in the specified week', ''],
    'FOVMain': ['Percent', 'Km of mains covered over the total Km of mains', 'DistributionPipeCoveredKm / DistributionPipeKm'],
    'SurveyDurationHours': ['Hours', 'Total hours driven by all cars in the week', ''],
    'TargetDurationHours': ['Hours', 'Exepected total number hours driven by all cars available. i.e 7 days * 7 hours * 25 cars', ''],
    'CustomerUtilization': ['Percent', 'Total hours driven by all cars in the week over the expected total number hours driven by all cars available. i.e 7 days * 7 hours * 25 cars', 'SurveyDurationHours / TargetDurationHours'],
    'StarndardUtilization': ['Percent', 'Total hours driven by all cars in the week over the expected total number hours driven by all cars available. i.e 6 days * 5 hours * 25 cars', 'SurveyDurationHours / TargetDurationHours'],
    'TotalSurveyors': ['Surveyor', 'Total number of surveyors in the specified week', ''],
    'ProductivityPerSurveyor': ['Km / Surveyor', 'Total length of all the assets covered in the report over the total number of surveyors in the specified week', 'DistributionPipeCoveredKm / TotalSurveyors'],
    'SurveyCount': ['Survey', 'Total number of surveys in the  specified week', ''],
    'AvgSpeedKm': ['Km/h', 'Average speed counting all the cars in the specified week', ''],
    'SurveysCarDay': ['Survey / Car / Day', 'Total number of surveys per car per day in the specified week', 'SurveyCount / TotalSurveyors / DaysCount'],
    'IdleTime': ['Percent', 'Ratio of idle time over the total survey duration', 'IdleTimeMinutes / SurveyDurationMinutes'],
    'TotalDrivenLengthKm': ['Km', 'Total length driven in the specified week', ''],
    'DrivingRatio': ['Ratio', 'Total length driven in the specified week over Total length of all the assets covered in the report', 'TotalKilometers / DistributionPipeCoveredKm'],
    'NightDrivenLength': ['Km', 'Total length covered during the night in the specified week', ''],
    'DayDrivenLength': ['Km', 'Total length covered during the day in the specified week', ''],
    'NightRatio': ['Percent', 'NightKm / TotalKilometers', ''],
    'DayRatio': ['Percent', 'DayKm / TotalKilometers', ''],
    'PeakAboveSATCount': ['Peak', 'Total number of peaks above SAT in the specified week', ''],
    'LisaCount': ['Lisa', 'Total number of Lisa in the specified week, (No Disposition 2)', ''],
    'EmissionRate': ['SCFH', 'Total emission rate in the specified week, (No Disposition 2)', ''],
    'B0Count': ['Lisa', 'Total number of B0 in the specified week, (No Disposition 2)', ''],
    'B1Count': ['Lisa', 'Total number of B1 in the specified week, (No Disposition 2)', ''],
    'Bm1Count': ['Lisa', 'Total number of B-1 in the specified week, (No Disposition 2)', ''],
    'Bm2Count': ['Lisa', 'Total number of B-2 in the specified week, (No Disposition 2)', ''],
    'NGCount': ['Lisa', 'Total number of NG in the specified week, (With Disposition 2)', ''],
    'PGCount': ['Lisa', 'Total number of PG in the specified week, (With Disposition 2)', ''],
    'Not_NGCount': ['Lisa', 'Total number of Not NG in the specified week, (With Disposition 2)', ''],
    'LisaDensity': ['Lisa / Km', 'Number of Lisa per Km of Asset Covered', 'LisaCount / DistributionPipeCoveredKm'],
    'InstatanoeusEmission': ['SCFH / Km', 'Emission rate per Km of Asset Covered', 'EmissionRate / DistributionPipeCoveredKm'],
    'B0Density': ['Lisa / Km', 'Number of B0 per Km of Asset Covered', 'B0Count / DistributionPipeCoveredKm'],
    'B1Density': ['Lisa / Km', 'Number of B1 per Km of Asset Covered', 'B1Count / DistributionPipeCoveredKm'],
    'Bm1Density': ['Lisa / Km', 'Number of B-1 per Km of Asset Covered', 'Bm1Count / DistributionPipeCoveredKm'],
    'Bm2Density': ['Lisa / Km', 'Number of B-2 per Km of Asset Covered', 'Bm2Count / DistributionPipeCoveredKm'],
    'B0Share': ['Percent', 'Number of B0 per Lisa', 'B0Count / LisaCount'],
    'B1Share': ['Percent', 'Number of B1 per Lisa', 'B1Count / LisaCount'],
    'Bm1Share': ['Percent', 'Number of B-1 per Lisa', 'Bm1Count / LisaCount'],
    'Bm2Share': ['Percent', 'Number of B-2 per Lisa', 'Bm2Count / LisaCount'],
    'NGShare': ['Percent', 'Number of NG per Lisa', 'NGCount / (NGCount + Not_NGCount + PGCount)'],
    'PGShare': ['Percent', 'Number of PG per Lisa', 'PGCount / (NGCount + Not_NGCount + PGCount)'],
    'Not_NGShare': ['Percent', 'Number of Not NG per Lisa', 'Not_NGCount / (NGCount + Not_NGCount + PGCount)'],
    'POR': ['Km', 'Total Km of the POR in the year', ''],
    'CurrentCompletion': ['Percent', 'Current completion of the network based on the POR', 'CumulativeAssetCoveredLengthKm / POR']
}

kpi_df = pd.DataFrame(
    [
        {"Name": key, "Unit": value[0], "Description": value[1], "Formula": value[2], "LastUpdated": datetime.now()}
        for key, value in output_dict.items()
    ]
)

KPI_Definition.update_table(arguments={'DataFrame': kpi_df, 'db_path': DB_PATH, 'PrimaryKey': 'Name'})