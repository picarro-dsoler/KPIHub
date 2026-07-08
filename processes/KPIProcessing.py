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
from lib.kpi_processor.KPIReport import KPIReport, KPIEmissionSource, KPISurveySummary, KPIPeakSAT

from lib.KPIHubConnection import *
from lib.handlers.CustomerHandler import get_customer_list
from datetime import date
from datetime import timedelta
import pandas as pd

if __name__ == "__main__":

    customer = 'Cadent'
    aggregator = {'BoundaryRegion': 'BoundaryRegion'}

    reportKPI = KPIReport(customer)
    emissionSourceKPI = KPIEmissionSource(customer)
    surveyKPI = KPISurveySummary(customer)
    peakSATKPI = KPIPeakSAT(customer)
    POR_KPI = KPIPOR(customer)

    KPI_List = [reportKPI, emissionSourceKPI, surveyKPI, peakSATKPI]
    for KPI in KPI_List:
        KPI.query_table()
        KPI.process_data()
        KPI.push_data()

        print(KPI.data['output'])
        print(KPI.aggregator)

    