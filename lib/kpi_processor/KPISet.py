from locallib.picarrodb import *
from locallib.slack import *
from locallib.etl import Loggers

import os
import sys
import pandas as pd
from datetime import datetime, date, timedelta

# Get the absolute path of the current file's directory
directory = os.path.abspath(os.path.dirname(__file__))

# Just add the parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(directory, "..")))
sys.path.append(directory)
from tables.IngesterTables import *
from config import *
from KPIHubConnection import *
from query.bank import *

class KPISet:
    def __init__(self, name, customer_name = None, period = None):
        self.name = name
        self.tableDefinition = KPI_Definition
        self.tableData = KPI_Data
        self.customer_name = customer_name
        self.description = description
        self.unit = unit
        self.formula = formula
        #Test Query Result
        self.query_result = self.query_info()

        self.data = {}
        
    def query_info(self):
        query = f"SELECT * FROM {self.tableDefinition.name} WHERE Name = '{self.name}'"
        query_result = Query(query = query).execute([KPIHub_Conn])
        if query_result.empty or not (query_result['Name'] == self.name).any():
   
            raise ValueError(f"KPI {self.name} not found in Hub")  
        return query_result

    def _ingestor(self, arguments = None):
        #Query data eample
        if arguments is None:
            raise ValueError("Arguments are required")
        if 'tableList' not in arguments:
            raise ValueError("tableList is required")
        tableList = arguments['tableList']
        for table in tableList:
            self.data[table] = Query(query = f"SELECT * FROM {table.name} WHERE ReportId IN (SELECT ReportId FROM KPI_ReportSummary WHERE CustomerId IN (SELECT CustomerId FROM KPI_Customer WHERE Name = '{customer_name}'))").execute([KPIHub_Conn])

    def _aggregator(self, arguments = None):
        pass
    def _processor(self, arguments = None):
        pass
    
    def process_data(self, arguments = None):
        self._ingestor(arguments)
        self._processor(arguments)

    def write_to_db(self, arguments = None):
        if arguments is None:
            raise ValueError("Arguments are required")
        if 'data' not in arguments:
            raise ValueError("data is required")
        data = arguments['data']
        self.table.update_table(arguments = {'DataFrame': data, 'db_path': DB_PATH, 'PrimaryKey': 'Name'})