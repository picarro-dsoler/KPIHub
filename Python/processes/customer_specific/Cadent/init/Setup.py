import os
import sys
import pandas as pd

directory = os.path.abspath(os.path.dirname(__file__))
_root = os.path.abspath(os.path.join(directory, "..", "..", "..", ".."))

# Add KPIHub root to sys.path so `lib.*` imports resolve regardless of cwd.
sys.path.insert(0, _root)
os.chdir(_root)

import sqlite3

from locallib.picarrodb import *
from locallib.query import *

from lib.tables.IngesterTables import *
from lib.config import *
from lib.KPIHubConnection import *


#Create DB
db_path = os.path.abspath(os.path.join(_root, DB_PATH))
print(directory)
print(_root)
print(db_path)
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

conn.commit()

#Create Tables
#KPI Defintion table
KPI_Definition.reinit_table()
KPI_Data.reinit_table()
KPI_Utilization.reinit_table()
KPI_OutputExcelLocation.reinit_table()

#Customer Tables
KPI_Customer.reinit_table()
KPI_Country.reinit_table()
#POR Table
KPI_POR.reinit_table(arguments={'pair_key': ['CustomerId', 'Year']})
#Peak SAT Location Table
KPI_PeakSATLocation.reinit_table()
#SAT Tables
KPI_PeakAboveSAT.reinit_table()

#Summary Tables
KPI_SurveySummary.reinit_table(arguments = {'pair_key': ['SurveyId', 'ReportId']})
KPI_ReportSummary.reinit_table()
KPI_EmissionSourceSummary.reinit_table()
