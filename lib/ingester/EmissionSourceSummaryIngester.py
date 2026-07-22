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

class EmissionSourceSummaryIngester(Ingester):
    def __init__(self, arguments):
        super().__init__(arguments)
        self.table = KPI_EmissionSourceSummary

    def update_check(self):
        customer_name = self.customer_info['Name']
        customer_id = self.customer_info['CustomerId']
        customer_db = self.customer_info['DBLocation']

        self.Logger.info(f"Processing customer: {customer_name}")
        self.Logger.info(f"Getting reports from {self.update_window} to {self.current_date}")

        #Query the last report
        self.data['reports'] = Query(
            f"""
            SELECT ReportId, ReportDate, LastUpdated FROM KPI_ReportSummary
            WHERE CustomerId = '{customer_id}'
            ORDER BY LastUpdated DESC
            """
        ).execute(KPIHub_Conn)

        self.data['emissions_count'] = Query(
            f"""
            SELECT COUNT(*) as EmissionCount
            FROM KPI_EmissionSourceSummary
            WHERE ReportId IN (SELECT ReportId FROM KPI_ReportSummary WHERE CustomerId = '{customer_id}')
            """
        ).execute(KPIHub_Conn)
        self.Logger.info(f"Getting emissions from {self.update_window} to {self.current_date}")

        if len(self.data['reports']) > 0:
            if (self.data['emissions_count'].iloc[0]['EmissionCount']) > 0:
                self.check_flag = True
                self.starting_date = pd.to_datetime(self.update_window)

            else:
                self.Logger.info(f"No emissions found")
                self.starting_date = STARTING_DATE
                self.check_flag = True
        else:
            self.Logger.info(f"No reports found")
            self.check_flag = False

    def query_data(self):
        if self.check_flag:
            # Ensure the ReportDate values are in datetime format before comparison,
            # handling both with and without microseconds (mixed formats)
            self.data['reports']['ReportDate'] = pd.to_datetime(self.data['reports']['ReportDate'], format='mixed')
    
            reports_to_query = self.data['reports'][
                pd.to_datetime(self.data['reports']['ReportDate']).dt.date >= pd.to_datetime(self.starting_date).date()
            ]
            reports_to_query.db.set_query(query_emission_sources_table(report_table = '#TempReports'))
            emission_sources = reports_to_query.db.execute(CONN_DICT[self.customer_info['DBLocation']], source_col = 'ReportId', temp_table_name = '#TempReports')

            emissions_summary = emission_sources.groupby("ReportId").apply(summarize_emission).reset_index()
            emissions_summary.fillna(0, inplace=True)
            emissions_summary['LastUpdated'] = datetime.now()
            self.data['output'] = emissions_summary
        else:
            self.Logger.info(f"No reports found, skipping")

 
    def sanity_check(self):
        super().sanity_check()
        #Get all the reports from the KPI_SurveySummary table
        df_surveys = Query(query = f"SELECT DISTINCT ReportId FROM KPI_EmissionSourceSummary WHERE ReportId IN (SELECT ReportId FROM KPI_ReportSummary WHERE CustomerId = '{self.customer_info['CustomerId']}')").execute(KPIHub_Conn)
        self.Logger.info(f"Total number of unique reports from KPI_EmissionSourceSummary: {len(df_surveys)}")

def summarize_emission(group):
    # Remove all the rows in the group where Disposition == 2
    forCounts = group[group["Disposition"] != 2]
    forShares = group
    return pd.Series({
        "EmissionRate": forCounts["EmissionRate"].sum(),
        'RepresentativeEmissionRate': forCounts["RepresentativeEmissionRate"].mean(),
        "LisaCount": forCounts["EmissionSourceId"].count(),
        "B0Count": forCounts["RepresentativeBinLabel"].value_counts().get("B0"),
        "B1Count": forCounts["RepresentativeBinLabel"].value_counts().get("B1"),
        "Bm1Count": forCounts["RepresentativeBinLabel"].value_counts().get("B-1"),
        "Bm2Count": forCounts["RepresentativeBinLabel"].value_counts().get("B-2"),
        #'B0EmissionRate': forCounts[forCounts["RepresentativeBinLabel"] == "B0"]["EmissionRate"].sum(),
        #'B1EmissionRate': forCounts[forCounts["RepresentativeBinLabel"] == "B1"]["EmissionRate"].sum(),
        #'Bm1EmissionRate': forCounts[forCounts["RepresentativeBinLabel"] == "B-1"]["EmissionRate"].sum(),
        #'Bm2EmissionRate': forCounts[forCounts["RepresentativeBinLabel"] == "B-2"]["EmissionRate"].sum(),
        #'B0RepEmissionRate': forCounts[forCounts["RepresentativeBinLabel"] == "B0"]["RepresentativeEmissionRate"].mean(),
        #'B1RepEmissionRate': forCounts[forCounts["RepresentativeBinLabel"] == "B1"]["RepresentativeEmissionRate"].mean(),
        #'Bm1RepEmissionRate': forCounts[forCounts["RepresentativeBinLabel"] == "B-1"]["RepresentativeEmissionRate"].mean(),
        #'Bm2RepEmissionRate': forCounts[forCounts["RepresentativeBinLabel"] == "B-2"]["RepresentativeEmissionRate"].mean(),
        "Not_NGCount": forShares["Disposition"].value_counts().get(2),
        "PGCount": forShares["Disposition"].value_counts().get(3),
        "NGCount": forShares["Disposition"].value_counts().get(1),
    })


if __name__ == "__main__":
    arguments = {'conn': KPIHub_Conn}
    ingester = EmissionSourceSummaryIngesters(arguments)
    ingester.set_customer_info(ingester.customer_list.iloc[0])
    ingester.query_data()
    ingester.push_data()
    ingester.sanity_check()