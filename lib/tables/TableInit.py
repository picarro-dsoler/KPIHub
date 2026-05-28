from CustomerTables import *
from IngesterTables import *
# Initialize the tables
#Customer Tables
CustomerKPI.create_table(arguments={'db_path': '../../database/KPIHub.db'})

#Summary Tables
ReportSummary.create_table(arguments={'db_path': '../../database/KPIHub.db'})
EmissionSourceSummary.create_table(arguments={'db_path': '../../database/KPIHub.db'})
SurveySummary.create_table(arguments={'db_path': '../../database/KPIHub.db'})