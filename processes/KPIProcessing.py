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
from lib.kpi_processor.KPIReport import KPIReport, KPIEmissionSource, KPISurveySummary, KPIPeakSAT, KPIPOR

from lib.KPIHubConnection import *
from lib.handlers.CustomerHandler import get_customer_list
from datetime import date
from datetime import timedelta
import pandas as pd

if __name__ == "__main__":

    customer = 'Cadent'
    aggregator = {'BoundaryRegion': 'BoundaryRegion'}

    #Set the global KPI
    print("Setting the global KPI")
    reportKPI = KPIReport(customer)
    emissionSourceKPI = KPIEmissionSource(customer)
    surveyKPI = KPISurveySummary(customer)
    peakSATKPI = KPIPeakSAT(customer)
    POR_KPI = KPIPOR(customer)

    KPI_List = [reportKPI, emissionSourceKPI, surveyKPI, peakSATKPI, POR_KPI]
    for KPI in KPI_List:
        print(KPI)
        KPI.query_table()
        KPI.process_data()
        KPI.push_data()

        print(KPI.data['output'])
        print(KPI.aggregator)

    #Set the regional KPI
    print("Setting the regional KPI")
    reportKPI = KPIReport(customer, aggregator)
    emissionSourceKPI = KPIEmissionSource(customer, aggregator)
    surveyKPI = KPISurveySummary(customer, aggregator)
    peakSATKPI = KPIPeakSAT(customer, aggregator)
    KPI_List = [reportKPI, emissionSourceKPI, surveyKPI, peakSATKPI]
    for KPI in KPI_List:
        KPI.query_table()
        KPI.process_data()
        KPI.push_data()

        print(KPI.data['output'])
        print(KPI.aggregator)
