from locallib.picarrodb import *
from locallib.slack import *
from locallib.etl import Loggers

import os
import sys


# Get the absolute path of the current file's directory
directory = os.path.abspath(os.path.dirname(__file__))

# Just add the parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(directory, "..")))

#Ingester Processes
from lib.kpi_processor.KPIReport import KPIReport, KPIEmissionSource, KPISurveySummary

from lib.KPIHubConnection import *
from lib.handlers.CustomerHandler import get_customer_list
from datetime import date
from datetime import timedelta
import pandas as pd

if __name__ == "__main__":
   # reportKPI = KPIReport('Cadent', aggregator = {'BonudaryRegion': 'BoundaryRegion'})
   # reportKPI.query_table()
  #  reportKPI.process_data()
   # reportKPI.push_data()

    #print(reportKPI.data['output'])
   # print(reportKPI.aggregator)
    #emissionSourceKPI = KPIEmissionSource('Cadent')
    #emissionSourceKPI.query_table()
    #emissionSourceKPI.process_data()
    #emissionSourceKPI.push_data()

    #print(emissionSourceKPI.data['output'])
    #print(emissionSourceKPI.aggregator)

    surveyKPI = KPISurveySummary('Cadent', aggregator = {'BoundaryRegion': 'BoundaryRegion'})
    
    surveyKPI.query_table()
    surveyKPI.process_data()
    surveyKPI.push_data()

    print(surveyKPI.data['output'])
    print(surveyKPI.aggregator)