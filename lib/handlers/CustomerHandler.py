from locallib.picarrodb import *
from locallib.query import *

import os
import sys


# Get the absolute path of the current file's directory
directory = os.path.abspath(os.path.dirname(__file__))

# Just add the parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(directory, "..")))

from tables.IngesterTables import *
from config import *
from lib.KPIHubConnection import *
import pandas as pd
from datetime import datetime

def get_customer_list(Conn):
    query = f"SELECT * FROM KPI_Customer WHERE DBLocation IS NOT 'Unknown'"
    q = Query(query = query)
    return q.execute(Conn)

def add_customer_utilization(customer_name, working_hours = 0, working_days = 0, base_surveyor_count = 0, Conn = KPIHub_Conn):
    customer_id = Query(query = f"SELECT CustomerId FROM KPI_Customer WHERE Name = '{customer_name}'").execute(Conn)
    if customer_id.empty:
        raise ValueError(f"Customer {customer_name} not found")
    else:
        customer_id = customer_id.iloc[0]['CustomerId']
        data = pd.DataFrame({'CustomerId': [customer_id], 'WorkingHours': [working_hours], 'WorkingDays': [working_days], 'BaseSurveyorCount': [base_surveyor_count]})
        data['LastUpdated'] = datetime.now()
        KPI_Utilization.update_table(arguments = {'DataFrame': data, 'db_path': DB_PATH, 'PrimaryKey': ['CustomerId']})

def add_por(customer_name, year, value, unit = 'Km', Conn = KPIHub_Conn):
    customer_id = Query(query = f"SELECT CustomerId FROM KPI_Customer WHERE Name = '{customer_name}'").execute(Conn)
    if customer_id.empty:
        raise ValueError(f"Customer {customer_name} not found")
    else:
        customer_id = customer_id.iloc[0]['CustomerId']
        data = pd.DataFrame({'CustomerId': [customer_id], 'Year': [year], 'Value': [value], 'Unit': [unit]})
        data['LastUpdated'] = datetime.now()
        KPI_POR.update_table(arguments = {'DataFrame': data, 'db_path': DB_PATH, 'PrimaryKey': ['CustomerId', 'Year']})

def add_output_excel_location(customer_name, box_folder_id, Conn):
    customer_id = Query(query = f"SELECT CustomerId FROM KPI_Customer WHERE Name = '{customer_name}'").execute(Conn)
    if customer_id.empty:
        raise ValueError(f"Customer {customer_name} not found")
    else:
        customer_id = customer_id.iloc[0]['CustomerId']
        data = pd.DataFrame({'CustomerId': [customer_id], 'BoxFolderId': [box_folder_id]})
        data['LastUpdated'] = datetime.now()
        KPI_OutputExcelLocation.update_table(arguments = {'DataFrame': data, 'db_path': DB_PATH, 'PrimaryKey': ['CustomerId']})

def add_peak_sat_file_id(customer_name, file_id, Conn):
    customer_id = Query(query = f"SELECT CustomerId FROM KPI_Customer WHERE Name = '{customer_name}'").execute(Conn)
    if customer_id.empty:
        raise ValueError(f"Customer {customer_name} not found")
    else:
        customer_id = customer_id.iloc[0]['CustomerId']
        data = pd.DataFrame({'CustomerId': [customer_id], 'BoxFileId': [file_id]})
        data['LastUpdated'] = datetime.now()
        KPI_PeakSATLocation.update_table(arguments = {'DataFrame': data, 'db_path': DB_PATH, 'PrimaryKey': ['CustomerId']})

def add_customer(customer_name,Conn):
    result = Query(query = f"SELECT C.Id, C.Name FROM Customer C WHERE LOWER(C.Name) = LOWER('{customer_name}')").execute(Conn)
    if result.empty:
        raise ValueError(f"Customer {customer_name} not found")
    else:
        if Conn.database == 'EU-SurveyorProduction':
            DBLocation = 'EU1'
        elif Conn.database == 'EU-SurveyorProduction2':
            DBLocation = 'EU2'
        else:
            DBLocation = 'Unknown'
        short_name = result.iloc[0]['Name'].replace(" ", "")
        data = pd.DataFrame({
            'CustomerId': [result.iloc[0]['Id']],
            'Name': [result.iloc[0]['Name']],
            'ShortName': [short_name],
            'DBLocation': [DBLocation],
            'LastUpdated': [datetime.now()]
        })
        KPI_Customer.update_table(arguments={'DataFrame': data, 'db_path': DB_PATH, 'PrimaryKey': ['CustomerId']})