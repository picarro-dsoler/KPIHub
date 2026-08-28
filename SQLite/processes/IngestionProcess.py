import os
import sys

# Add the KPIHub directory to sys.path so all local packages resolve
directory = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(directory, "..")))

from locallib.picarrodb import *
from locallib.slack import *
from locallib.etl import Loggers

#Ingester Processes
from lib.ingester.ReportSummaryIngester import ReportSummaryIngester
from lib.ingester.ReportSummaryIngester import ReportSummaryListIngester
from lib.ingester.SurveySummaryIngester import SurveySummaryIngester
from lib.ingester.EmissionSourceSummaryIngester import EmissionSourceSummaryIngester
from lib.ingester.PeakSATIngester import PeakSATIngester

from lib.KPIHubConnection import *
from lib.handlers.CustomerHandler import get_customer_list
from datetime import date
from datetime import timedelta
import pandas as pd

if __name__ == "__main__":
    #file_list = {'ITALGAS': 2360359055921, 'Toscana Energia': 2362382199609}
    file_list = {}
    customer_list = get_customer_list(KPIHub_Conn)
    arguments = {'conn': KPIHub_Conn}
    for _,customer in customer_list.iterrows():
        if customer['Active'] == 0:
            continue
        if customer['Name'] in file_list:
            reportIngester = ReportSummaryListIngester(arguments, report_list=file_list[customer['Name']])
        else:
            reportIngester = ReportSummaryIngester(arguments)
        reportIngester.set_customer_info(customer)
        reportIngester.update_check()
        reportIngester.query_data()
        reportIngester.push_data()
        reportIngester.delete_data()
        reportIngester.sanity_check()

        surveyIngester = SurveySummaryIngester(arguments)
        surveyIngester.set_customer_info(customer)
        surveyIngester.update_check()
        surveyIngester.query_data()
        surveyIngester.push_data()
        surveyIngester.delete_data()
        surveyIngester.sanity_check()
        
        emissionSourceIngester = EmissionSourceSummaryIngester(arguments)
        emissionSourceIngester.set_customer_info(customer)
        emissionSourceIngester.update_check()
        emissionSourceIngester.query_data()
        emissionSourceIngester.push_data()
        emissionSourceIngester.delete_data()
        emissionSourceIngester.sanity_check()

        #if customer['Name'] == 'Cadent':
        #    peakSATIngester = PeakSATIngester(arguments)
        #    peakSATIngester.set_customer_info(customer)
        #    peakSATIngester.update_check()
        #    peakSATIngester.query_data()
        #    peakSATIngester.push_data()
        #    peakSATIngester.sanity_check()
