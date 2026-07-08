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
from IngesterClass import Ingester

from datetime import date
from datetime import timedelta

class PeakSATIngester(Ingester):
    def __init__(self, arguments):
        super().__init__(arguments)
        self.table = KPI_PeakSATLocation

    def update_check(self):
        self.Logger.info(f"Processing customer: {self.customer_info['Name']}")

        #Get the data from box
        data = Query(query = f"SELECT * FROM KPI_PeakSATLocation WHERE CustomerId = {self.customer_info['Id']}").execute(KPIHub_Conn)
        box_file_id = data.iloc[0]['BoxFileId']
        box_obj = BoxFile(local_path='temp.xlsx', box_file_id =box_file_id)
        box_obj.download()
        df = pd.read_excel('temp.xlsx')
        box_obj.delete()

        #Get the data from the database
        data = Query(query = f"SELECT * FROM KPI_PeakAboveSAT WHERE CustomerId = {self.customer_info['Id']}").execute(KPIHub_Conn)
        df_db = pd.DataFrame(data)
        if len(df_db) == 0:
            self.check_flag = True
            self.data['Box'] = df

        elif len(df_db) != len(df):
            self.check_flag = True
        else:
            self.check_flag = False

    def query_data(self):
        self.Logger.info(f"Querying data for customer: {self.customer_info['Name']}")
    
        if self.check_flag:
            self.data['Box']['CustomerId'] = self.customer_info['Id']
            self.data['Box']['ReportYear'] = self.data['Box']['Date'].dt.year
            self.data['Box']['LastUpdated'] = datetime.now()
            self.data['Box'].rename(columns = {'Region': 'BoundaryRegion'}, inplace = True)
            self.data['output'] = self.data['Box']

    def push_data(self):
        super().push_data(primary_key = ['PeakId'])
        self.Logger.info(f"Data pushed to {db_path}")

    def sanity_check(self):
        df_kpi = Query(query = f"SELECT * FROM KPI_PeakSAT WHERE CustomerId = '{self.customer_info['Id']}'").execute(KPIHub_Conn)
        self.Logger.info(f"Total number of peaks from file: {len(self.data['output'])}")
        self.Logger.info(f"Total number of unique peaks from KPI_PeakSAT: {len(df_kpi)}")