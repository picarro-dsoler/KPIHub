import os
import sys
import pandas as pd
# Get the absolute path of the current file's directory
directory = os.path.abspath(os.path.dirname(__file__))

# Just add the parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(directory, "..")))

from config import *
from locallib.picarrodb import *
from locallib.pandas import *
from locallib.slack import *
from locallib.etl import Loggers

import logging
import os
#Class used to get any data inside the data KPI HUb database
# The inggester focuses on a single table at a time

#Add sanity checks to ensure that all what you have on P-Cubed are the same things you have on KPIHUb
class Ingester:
    def __init__(self, arguments):
        name = self.__class__.__name__
        LOG_PATH = os.path.abspath(os.path.join(directory, "..", "..", INGESTER_LOG_PATH, f'{name}.log'))
        Logger = Loggers(logger_name = name, keys = ['File', 'Slack'])
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
        self.Logger.info(f"{name} initialized")

    def query_data(self):
        self.Logger.info(f"Querying data for {self.name}")
        pass

    def process_data(self):
        self.Logger.info(f"Transforming data for {self.name}")
        pass

    def push_data(self):
        self.Logger.info(f"Loading data for {self.name}")
        pass

    def sanity_check(self):
        self.Logger.info(f"Sanity checking data for {self.name}")
        pass


class EmissionSourceIngester(Ingester):
    def __init__(self, resource):
        super().__init__(resource)

    def pull_data(self):
        pass

class SurveyIngester(Ingester):
    def __init__(self, resource):
        super().__init__(resource)

    def pull_data(self):
        pass

class LeakIngester(Ingester):
    def __init__(self, resource):
        super().__init__(resource)

    def pull_data(self):
        pass