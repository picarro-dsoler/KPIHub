import os
import sys


# Get the absolute path of the current file's directory
directory = os.path.abspath(os.path.dirname(__file__))
# Just add the parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(directory, "..")))

from locallib.picarrodb import *
from locallib.slack import *
from locallib.etl import Loggers


#Ingester Processes
from lib.kpi_processor.KPIReport import KPIReport, KPIEmissionSource, KPISurveySummary, KPIPeakSAT, KPIPOR

from lib.KPIHubConnection import *
from lib.handlers.CustomerHandler import get_customer_list
from datetime import date
from datetime import timedelta
import pandas as pd

if __name__ == "__main__":

    customer_list = get_customer_list(KPIHub_Conn)
    for _, customer in customer_list.iterrows():
        print("--------------------------------")
        print(customer['Name'])
        customer_name = customer['Name']
        aggregator = {'BoundaryRegion': 'BoundaryRegion'}

        #Set the global KPI 
        print("Setting the global KPI Weekly")
        reportKPI = KPIReport(customer_name)
        emissionSourceKPI = KPIEmissionSource(customer_name)
        surveyKPI = KPISurveySummary(customer_name)
        POR_KPI = KPIPOR(customer_name)
        if customer['Name'] == 'Cadent':
            peakSATKPI = KPIPeakSAT(customer_name)
            KPI_List = [reportKPI, emissionSourceKPI, surveyKPI, peakSATKPI, POR_KPI]
        else:
            KPI_List = [reportKPI, emissionSourceKPI, surveyKPI, POR_KPI]
        try:
            for KPI in KPI_List:
                print(KPI.name)
                KPI.query_table()
                KPI.process_data()
                KPI.push_data()
            print("Global KPI set successfully")
        except Exception as e:
            print(f"Error setting the global KPI for {customer_name}: {e}")
            print("--------------------------------")
        print("--------------------------------")

        #Set the regional KPI
        print("Setting the regional KPI Weekly")
        try:
            reportKPI = KPIReport(customer_name, aggregator)
            emissionSourceKPI = KPIEmissionSource(customer_name, aggregator)
            surveyKPI = KPISurveySummary(customer_name, aggregator)
            if customer['Name'] == 'Cadent':
                peakSATKPI = KPIPeakSAT(customer_name, aggregator)
                KPI_List = [reportKPI, emissionSourceKPI, surveyKPI, peakSATKPI]
            else:
                KPI_List = [reportKPI, emissionSourceKPI, surveyKPI]
            for KPI in KPI_List:
                print(KPI.name)
                KPI.query_table()
                KPI.process_data()
                KPI.push_data()
        except Exception as e:
            print(f"Error setting the regional KPI for {customer_name}: {e}")
            print("--------------------------------")


        #Set the global KPI Yearly
        print("Setting the global KPI Yearly")
        try:
            reportKPI = KPIReport(customer_name, period_dict={})
            emissionSourceKPI = KPIEmissionSource(customer_name, period_dict={})
            surveyKPI = KPISurveySummary(customer_name, period_dict={})
            if customer['Name'] == 'Cadent':
                peakSATKPI = KPIPeakSAT(customer_name, period_dict={})
                KPI_List = [reportKPI, emissionSourceKPI, surveyKPI, peakSATKPI]
            else:
                KPI_List = [reportKPI, emissionSourceKPI, surveyKPI]
            for KPI in KPI_List:
                print(KPI.name)
                KPI.query_table()
                KPI.process_data()
                KPI.push_data()
        except Exception as e:
            print(f"Error setting the global KPI Yearly for {customer_name}: {e}")
            print("--------------------------------")

        #Set the regionalKPI Yearly
        print("Setting the regional KPI Yearly")
        try:
            reportKPI = KPIReport(customer_name, aggregator, period_dict={})
            emissionSourceKPI = KPIEmissionSource(customer_name, aggregator, period_dict={})
            surveyKPI = KPISurveySummary(customer_name, aggregator, period_dict={})
            if customer['Name'] == 'Cadent':
                peakSATKPI = KPIPeakSAT(customer_name, aggregator, period_dict={})
                KPI_List = [reportKPI, emissionSourceKPI, surveyKPI, peakSATKPI]
            else:
                KPI_List = [reportKPI, emissionSourceKPI, surveyKPI]
            for KPI in KPI_List:
                print(KPI.name)
                KPI.query_table()
                KPI.process_data()
                KPI.push_data()
        except Exception as e:
            print(f"Error setting the regional KPI Yearly for {customer_name}: {e}")
            print("--------------------------------")