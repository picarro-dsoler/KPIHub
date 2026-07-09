import os
import sys

directory = os.path.abspath(os.path.dirname(__file__))
_root = os.path.abspath(os.path.join(directory, "..", ".."))

# Add KPIHub root to sys.path so `lib.*` imports resolve regardless of cwd.
sys.path.insert(0, _root)
os.chdir(_root)

from locallib.picarrodb import *
from locallib.slack import *
from locallib.etl import Loggers
from locallib.box import *

import pandas as pd
from datetime import datetime, date, timedelta

from lib.tables.IngesterTables import *
from lib.config import *
from lib.KPIHubConnection import *
from lib.query.bank import *
from lib.ingester.IngesterClass import Ingester
from lib.handlers.CustomerHandler import get_customer_list

class PeakSATIngester(Ingester):
    def __init__(self, arguments):
        super().__init__(arguments)
        self.table = KPI_PeakAboveSAT

    def update_check(self):
        self.Logger.info(f"Processing customer: {self.customer_info['Name']}")
    
        #Get the data from box
        data = Query(query = f"SELECT * FROM KPI_PeakSATLocation WHERE CustomerId = '{self.customer_info['CustomerId']}'").execute(KPIHub_Conn)
        box_file_id = data.iloc[0]['BoxFileId']
        box_obj = BoxFile(local_path='temp.xlsx', box_file_id =box_file_id)
        box_obj.download()
        df = pd.read_excel('temp.xlsx')
        box_obj.delete()

        #Get the data from the database
        data = Query(query = f"SELECT * FROM KPI_PeakAboveSAT WHERE CustomerId = '{self.customer_info['CustomerId']}'").execute(KPIHub_Conn)
        df_db = pd.DataFrame(data)
        if len(df_db) == 0:
            self.Logger.info(f"No data found in KPI_PeakAboveSAT for customer: {self.customer_info['Name']}")
            self.check_flag = True
            self.data['Box'] = df
        elif len(df_db) != len(df):
            self.Logger.info(f"Data mismatch in KPI_PeakAboveSAT for customer: {self.customer_info['Name']}")
            self.Logger.info(f"Number of rows in KPI_PeakAboveSAT: {len(df_db)}")
            self.Logger.info(f"Number of rows in Box: {len(df)}")
            self.check_flag = True
        else:
            self.Logger.info(f"Data matches in KPI_PeakAboveSAT for customer: {self.customer_info['Name']}")
            self.Logger.info(f"Number of rows in KPI_PeakAboveSAT: {len(df_db)}")
            self.Logger.info(f"Number of rows in Box: {len(df)}")
            self.check_flag = False

    def query_data(self):
        self.Logger.info(f"Querying data for customer: {self.customer_info['Name']}")
        if self.check_flag:
            self.data['Box']['CustomerId'] = self.customer_info['CustomerId']
            self.data['Box']['ReportYear'] = self.data['Box']['Date'].dt.year
            self.data['Box']['LastUpdated'] = datetime.now()
            self.data['Box'].rename(columns = {'Region': 'BoundaryRegion'}, inplace = True)
            self.data['output'] = self.data['Box']

    def push_data(self):
        super().push_data(primary_key = ['PeakId'])
        self.Logger.info(f"Data pushed to {db_path}")

    def sanity_check(self):
        df_kpi = Query(query = f"SELECT * FROM KPI_PeakAboveSAT WHERE CustomerId = '{self.customer_info['CustomerId']}'").execute(KPIHub_Conn)
        self.Logger.info(f"Total number of peaks from KPI_PeakAboveSAT: {len(df_kpi)}")

if __name__ == "__main__":
    customer_list = get_customer_list(KPIHub_Conn)
    arguments = {'conn': KPIHub_Conn}
    peakSATIngester = PeakSATIngester(arguments)
    peakSATIngester.set_customer_info(customer_list.iloc[0])
    peakSATIngester.update_check()
    peakSATIngester.query_data()
    peakSATIngester.push_data()
    peakSATIngester.sanity_check()