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

SCFH_TO_SLPM_FACTOR = 0.471947


class EmissionSourceSummaryIngester(Ingester):
    def __init__(self, arguments):
        super().__init__(arguments)
        self.table = KPI_EmissionSourceSummary

    def update_check(self):
        customer_name = self.customer_info['Name']
        customer_id = self.customer_info['CustomerId']
        customer_db = self.customer_info['DBLocation']

        self.Logger.info(f"Processing customer: {customer_name}")
        
        #Query the reports from KPI_EmissionSources
        query_kpi_emission_sources = f"""SELECT ReportId FROM KPI_EmissionSourceSummary WHERE ReportId IN (SELECT ReportId FROM KPI_ReportSummary WHERE CustomerId = '{self.customer_info['CustomerId']}')"""
        reports_kpi_emission_sources = Query(query = query_kpi_emission_sources).execute(KPIHub_Conn)
        num_reports_kpi_emission_sources = len(reports_kpi_emission_sources)

        #Query the reports from KPI_ReportSummary
        query_kpi_report = f"""SELECT ReportId FROM KPI_ReportSummary WHERE CustomerId = '{self.customer_info['CustomerId']}'"""
        reports_kpi_hub = Query(query = query_kpi_report).execute(KPIHub_Conn)
 
        num_reports_kpi_hub = len(reports_kpi_hub)

        #Check if there are new reports
        reports_into = reports_kpi_hub[~reports_kpi_hub['ReportId'].isin(reports_kpi_emission_sources['ReportId'])]
        reports_deleted = reports_kpi_emission_sources[~reports_kpi_emission_sources['ReportId'].isin(reports_kpi_hub['ReportId'])]

        self.data['reports_into'] = reports_into.copy()
        self.data['reports_deleted'] = reports_deleted.copy()
        self.data['num_reports_kpi_emission_sources'] = num_reports_kpi_emission_sources
        self.data['num_reports_kpi_hub'] = num_reports_kpi_hub

        if (num_reports_kpi_hub > 0):
            self.Logger.info(f"Number of reports in KPI_ReportSummary: {num_reports_kpi_hub}")
            if(num_reports_kpi_emission_sources == 0):
                #No reports in the KPI_EmissionSources
                self.Logger.info("No reports in KPIHub, starting from the beginning")
                self.check_flag = True
            else:
                #Reports in the KPIHub
                self.Logger.info(f"Number of reports in KPI_EmissionSources: {num_reports_kpi_emission_sources}")
                if len(reports_into) > 0 or len(reports_deleted) > 0:
                    self.Logger.info(f"Number of new reports into the KPI_EmissionSources: {len(reports_into)}")
                    self.Logger.info(f"Number of deleted reports in the KPI_ReportSummary: {len(reports_deleted)}")
                    self.check_flag = True
                else:
                    self.Logger.info("No new reports into the KPI_EmissionSources or deleted reports in the KPI_EmissionSources")
                    self.check_flag = False
        else:
            self.Logger.info("No reports in KPI_ReportSummary")
            self.check_flag = False

    def query_data(self):
        if self.check_flag and len(self.data['reports_into']) > 0:
            reports_to_query = self.data['reports_into'].copy()
            reports_to_query.db.set_query(query_emission_sources_table(report_table = '#TempReports'))
            emission_sources = reports_to_query.db.execute(CONN_DICT[self.customer_info['DBLocation']], source_col = 'ReportId', temp_table_name = '#TempReports')
            emissions_summary = emission_sources.groupby("ReportId").apply(summarize_emission).reset_index()
            # Merge with reports_to_query to fill zeros for missing emission records per report
            merged_reports = reports_to_query[['ReportId']].merge(emissions_summary, on="ReportId", how="left")
            merged_reports.fillna(0, inplace=True)
    
            merged_reports['LastUpdated'] = datetime.now()
            self.data['output'] = merged_reports
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
    forPCChecks = group[group["IsFiltered"] == 0 & (group["Disposition"] != 2)]
    forShares = group
    return pd.Series({
        "EmissionRate": forCounts["EmissionRate"].sum(),
        "EmissionRateLPM": forCounts["EmissionRate"].sum() * SCFH_TO_SLPM_FACTOR,
        'RepresentativeEmissionRate': forCounts["RepresentativeEmissionRate"].sum(),
        'RepresentativeEmissionRateLPM': forCounts["RepresentativeEmissionRate"].sum() * SCFH_TO_SLPM_FACTOR,
        "LisaCount": forCounts["EmissionSourceId"].count(),
        "LisaPSCount": forPCChecks["EmissionSourceId"].count(),
        "B0Count": forCounts["RepresentativeBinLabel"].value_counts().get("B0"),
        "B1Count": forCounts["RepresentativeBinLabel"].value_counts().get("B1"),
        "Bm1Count": forCounts["RepresentativeBinLabel"].value_counts().get("B-1"),
        "Bm2Count": forCounts["RepresentativeBinLabel"].value_counts().get("B-2"),
        'B0RepEmissionRateLPM': forCounts[forCounts["RepresentativeBinLabel"] == "B0"]["RepresentativeEmissionRate"].sum() * SCFH_TO_SLPM_FACTOR,
        'B1RepEmissionRateLPM': forCounts[forCounts["RepresentativeBinLabel"] == "B1"]["RepresentativeEmissionRate"].sum() * SCFH_TO_SLPM_FACTOR,
        'Bm1RepEmissionRateLPM': forCounts[forCounts["RepresentativeBinLabel"] == "B-1"]["RepresentativeEmissionRate"].sum() * SCFH_TO_SLPM_FACTOR,
        'Bm2RepEmissionRateLPM': forCounts[forCounts["RepresentativeBinLabel"] == "B-2"]["RepresentativeEmissionRate"].sum() * SCFH_TO_SLPM_FACTOR,
        'B0RepEmissionRate': forCounts[forCounts["RepresentativeBinLabel"] == "B0"]["RepresentativeEmissionRate"].sum(),
        'B1RepEmissionRate': forCounts[forCounts["RepresentativeBinLabel"] == "B1"]["RepresentativeEmissionRate"].sum(),
        'Bm1RepEmissionRate': forCounts[forCounts["RepresentativeBinLabel"] == "B-1"]["RepresentativeEmissionRate"].sum(),
        'Bm2RepEmissionRate': forCounts[forCounts["RepresentativeBinLabel"] == "B-2"]["RepresentativeEmissionRate"].sum(),
        "Not_NGCount": forShares["Disposition"].value_counts().get(2),
        "PGCount": forShares["Disposition"].value_counts().get(3),
        "NGCount": forShares["Disposition"].value_counts().get(1),
    })


if __name__ == "__main__":
    arguments = {'conn': KPIHub_Conn}
    ingester = EmissionSourceSummaryIngester(arguments)
    ingester.set_customer_info(ingester.customer_list.iloc[0])
    ingester.query_data()
    ingester.push_data()
    ingester.sanity_check()