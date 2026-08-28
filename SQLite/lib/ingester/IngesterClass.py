import os
import sys
import pandas as pd
# IngesterClass.py lives at KPIHub/SQLite/lib/ingester/
directory = os.path.abspath(os.path.dirname(__file__))
KPIHUB_ROOT = os.path.abspath(os.path.join(directory, "..", ".."))

# Just add the parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(directory, "..")))

from config import *
from KPIHubConnection import *

from locallib.picarrodb import *
from locallib.pandas import *
from locallib.slack import *
from locallib.etl import Loggers

import logging
import os
from datetime import date, timedelta
from query.bank import *

#Class used to get any data inside the data KPI HUb database
# The inggester focuses on a single table at a time

#Add sanity checks to ensure that all what you have on P-Cubed are the same things you have on KPIHUb
class Ingester:
    def __init__(self, arguments):
        #Start the logger
        self.name = self.__class__.__name__
        log_dir = os.path.join(KPIHUB_ROOT, INGESTER_LOG_PATH)
        os.makedirs(log_dir, exist_ok=True)
        LOG_PATH = os.path.join(log_dir, f'{self.name}.log')
        Logger = Loggers(logger_name = self.name, keys = ['File', 'Slack'])
        Logger.clear_handlers()

        file_handler = logging.FileHandler(LOG_PATH)
        # Set date format to dd-mm-yyyy in log output
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s', datefmt='%d-%m-%Y')
        file_handler.setFormatter(formatter)
        Logger.File.addHandler(file_handler)

        slack_handler = logging.StreamHandler(SlackWriter(channel = 'C0B9PGDNHH7'))

        Logger.Slack.addHandler(slack_handler)
        self.Logger = Logger
        self.arguments = arguments
        self.Logger.info("="*100)
        self.Logger.info(f"{self.name} initialized")


        self.update_window = self.get_update_window()
        self.current_date = date.today()
        self.starting_date = STARTING_DATE
        self.check_status = False
        self.data = {}
        
        self.customer_info = None

    def get_update_window(self):
        current_date = date.today()
        update_window = current_date - timedelta(days=UPDATE_WINDOW_DAYS)
        return update_window
    
    def set_customer_info(self, customer_info):
        self.customer_info = customer_info

    def update_check(self):
        pass

    def query_data(self):
        self.Logger.info(f"Querying data for {self.name}")
        
        pass

    def process_data(self):
        self.Logger.info(f"Transforming data for {self.name}")
        pass

    def push_data(self, primary_key = 'ReportId'):
        db_path = os.path.join(KPIHUB_ROOT, DB_PATH)
        if self.check_flag:
            # Fix db path to go two parent folders before pointing to database/KPIHUB.db
            if len(self.data['reports_into']) > 0:
                self.table.update_table(arguments = {'db_path': db_path, 'DataFrame': self.data['output'], 'PrimaryKey': primary_key})
                self.Logger.info(f"Data pushed to {db_path}")
        else:
            self.Logger.info(f"No data to push")

    def delete_data(self, primary_key = 'ReportId'):
        db_path = os.path.join(KPIHUB_ROOT, DB_PATH)
        if self.check_flag:
            if len(self.data['reports_deleted']) > 0:
                self.table.delete_data(arguments = {'db_path': db_path, 'PrimaryKey': primary_key, 'KeyValues': self.data['reports_deleted']})
                self.Logger.info(f"Data deleted from {db_path}")
            else:
                self.Logger.info(f"No data to delete")
        else:
            self.Logger.info(f"No data to delete")


    def sanity_check(self):
        self.Logger.info(f"Sanity checking data for {self.name}")
        lsdb_report_count = Query(query = f"""
            SELECT DISTINCT R.Id 
            FROM Report R
            INNER JOIN ReportLabel RL ON RL.ReportId = R.Id
            INNER JOIN Label L ON RL.LabelId = L.Id
            WHERE R.CustomerId = '{self.customer_info['CustomerId']}'
              AND R.DateStarted >= '{STARTING_DATE}'
              AND L.Title = 'Final Checkbox'
              AND RL.IsActive = 1
        """).execute(CONN_DICT[self.customer_info['DBLocation']])
        self.Logger.info(f"Total reports on LSDB: {len(lsdb_report_count)}")

