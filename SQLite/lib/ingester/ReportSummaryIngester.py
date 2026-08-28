from locallib.picarrodb import *
from locallib.slack import *
from locallib.etl import Loggers
from locallib.box import BoxFile

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

class ReportSummaryIngester(Ingester):
    def __init__(self, arguments):
        super().__init__(arguments)
        self.table = KPI_ReportSummary

    def update_check(self):
        self.Logger.info(f"Processing customer: {self.customer_info['Name']}")
     # Query to get the number of different ReportId from reports from the very beggining
        query =   f"""SELECT R.Id as ReportId FROM
            Report R
        LEFT JOIN Customer C ON
            R.CustomerId = C.Id
        LEFT JOIN ReportLabel RL ON
            R.Id = RL.ReportId
        LEFT JOIN Label L ON
            RL.LabelId = L.Id
        LEFT JOIN ReportType ON
            R.ReportTypeId = ReportType.Id
        LEFT JOIN ReportArea RA ON R.Id = RA.ReportId
        LEFT JOIN ReportCompliance RC ON R.Id = RC.ReportId
        LEFT JOIN ReportAreaCovered RAC ON R.Id = RAC.ReportId
        WHERE
            R.CustomerId = '{self.customer_info['CustomerId']}' AND R.DateStarted >= '{self.starting_date}' AND L.Title = 'Final Checkbox' AND RL.IsActive = 1
            AND L.Title = 'Final Checkbox'
            AND RL.IsActive = 1
        """
        reports_list_lsdb = Query(query =query).execute(CONN_DICT[self.customer_info['DBLocation']])
        num_reports_lsdb = len(reports_list_lsdb)

        #Query the reports from the KPIHub
        query_kpi_report = f"""SELECT ReportId FROM KPI_ReportSummary WHERE CustomerId = '{self.customer_info['CustomerId']}'"""
        reports_kpi_hub = Query(query = query_kpi_report).execute(KPIHub_Conn)
        num_reports_kpi_hub = len(reports_kpi_hub)
        reports_into = reports_list_lsdb[~reports_list_lsdb['ReportId'].isin(reports_kpi_hub['ReportId'])]
        reports_deleted = reports_kpi_hub[~reports_kpi_hub['ReportId'].isin(reports_list_lsdb['ReportId'])]

        self.data['reports_into'] = reports_into
        self.data['reports_deleted'] = reports_deleted
        self.data['num_reports_lsdb'] = num_reports_lsdb
        self.data['num_reports_kpi_hub'] = num_reports_kpi_hub

        
        if (num_reports_lsdb > 0):
            self.Logger.info(f"Number of reports in LSDB: {num_reports_lsdb}")
            if(num_reports_kpi_hub == 0):
                #No reports in the KPIHub
                self.Logger.info("No reports in KPIHub, starting from the beginning")
                self.check_flag = True
            else:
                #Reports in the KPIHub
                self.Logger.info(f"Number of reports in KPIHub: {num_reports_kpi_hub}")
                if len(reports_into) > 0 or len(reports_deleted) > 0:
                    self.Logger.info(f"Number of new reports into the KPIHub: {len(reports_into)}")
                    self.Logger.info(f"Number of deleted reports in the KPIHub: {len(reports_deleted)}")
                    self.check_flag = True
                else:
                    self.Logger.info("No new reports into the KPIHub or deleted reports in the KPIHub")
                    self.check_flag = False
        else:
            self.Logger.info("No reports in LSDB")
            self.check_flag = False

    def query_data(self):
        DATAHUB_COLS = ['ReportId', 'BoundaryName', 'BoundaryType', 'BoundaryMode', 'BoundaryPlant', 'BoundarySubplant', 'BoundaryRegion', 'BoundarySubRegion']
        LSDB_COLS = [
                'ReportId',
                'CustomerId',
                'ReportName',
                'ReportDate',
                'ReportYear',
                'ReportMonth',
                'ReportWeek',
                'ReportAssetLengthKm',
                'AssetCoveredLengthKm',
                'DistributionPipeKm',
                'DistributionPipeCoveredKm',
                'ServicePipeKm',
                'ServicePipeCoveredKm',
                'ReportArea',
            ]
        if self.check_flag and len(self.data['reports_into']) > 0:
            if len(self.data['reports_into']) == self.data['num_reports_lsdb']:
                self.Logger.info(f"Updating reports")
                query = get_reports(self.customer_info['Name'], starting_date=self.starting_date, final_checkbox = True)
                reports_lsdb = query.execute(CONN_DICT[self.customer_info['DBLocation']])
            else:
                reports_temp = self.data['reports_into'].copy()
                reports_temp.db.set_query(get_reports(self.customer_info['Name'], starting_date=self.starting_date, report_id_table = '#TempReport', final_checkbox = True))
                reports_lsdb = reports_temp.db.execute(CONN_DICT[self.customer_info['DBLocation']], source_col = 'ReportId', temp_table_name = '#TempReport')
            if self.customer_info['DBLocation'] == 'EU1' or self.customer_info['DBLocation'] == 'EU2':
                reports_lsdb.db.set_query(query_reports_view(report_table = 'temp_reports'))
                reports_datahub = reports_lsdb.db.execute(DATAHUB_Conn, source_col = 'ReportId', temp_table_name = 'temp_reports')
                # Clisify (classify) the report_summary by different periods using to_period: quarter, year, month, week
                #report_summary['ReportQuarter'] = pd.to_datetime(report_summary['ReportDate']).dt.isocalendar().quarter
                reports_lsdb['ReportYear'] = pd.to_datetime(reports_lsdb['ReportDate']).dt.year
                reports_lsdb['ReportMonth'] = pd.to_datetime(reports_lsdb['ReportDate']).dt.month
                reports_lsdb['ReportWeek'] = pd.to_datetime(reports_lsdb['ReportDate']).dt.isocalendar().week
                reports = pd.merge(reports_lsdb[LSDB_COLS], reports_datahub[DATAHUB_COLS], on = 'ReportId', how = 'left')
            else:
                reports['ReportYear'] = pd.to_datetime(reports['ReportDate']).dt.year
                reports['ReportMonth'] = pd.to_datetime(reports['ReportDate']).dt.month
                reports['ReportWeek'] = pd.to_datetime(reports['ReportDate']).dt.isocalendar().week
                reports = reports_lsdb[LSDB_COLS]
            # Add/update the LastUpdated column to the reports DataFrame as current timestamp
            reports['LastUpdated'] = datetime.now()
            self.data['output'] = reports


    def sanity_check(self):
        super().sanity_check()
        df_kpi = Query(query = f"SELECT * FROM KPI_ReportSummary WHERE CustomerId = '{self.customer_info['CustomerId']}'").execute(KPIHub_Conn)
        self.Logger.info(f"Total reports from KPI_ReportSummary: {len(df_kpi)}")



class ReportSummaryListIngester(ReportSummaryIngester):
    def __init__(self, arguments, report_list=None):
        super().__init__(arguments)
        self.report_list = report_list
    
    def update_check(self):
        self.Logger.info(f"Processing customer: {self.customer_info['Name']}")
        self.check_flag = True

    def query_data(self, report_list=None):
        self.Logger.info(f"Querying data for {self.name}")
        if report_list is None:
            report_list = self.report_list
        LSDB_COLS = [
                'ReportId',
                'CustomerId',
                'ReportName',
                'ReportDate',
                'ReportYear',
                'ReportMonth',
                'ReportWeek',
                'ReportAssetLengthKm',
                'AssetCoveredLengthKm',
                'DistributionPipeKm',
                'DistributionPipeCoveredKm',
                'ServicePipeKm',
                'ServicePipeCoveredKm',
                'ReportArea',
            ]

        DATAHUB_COLS = ['ReportId', 'BoundaryName', 'BoundaryType', 'BoundaryMode', 'BoundaryPlant', 'BoundarySubplant', 'BoundaryRegion', 'BoundarySubRegion']
        if self.check_flag:
            box_obj = BoxFile(local_path = 'report_list.xlsx', box_file_id = report_list)
            box_obj.download()
            report_name = pd.read_excel('report_list.xlsx')
            box_obj.delete()
            print(len(report_name))
            print('Box file downloaded')
            report_name.db.set_query(query_reports_view_by_name(report_table = 'temp_reports'))
            reports_dh = report_name.db.execute(DATAHUB_Conn, source_col = 'ReportName', temp_table_name = 'temp_reports')
            reports_dh = reports_dh[DATAHUB_COLS]
            reports_dh['ReportId'] = reports_dh['ReportId'].astype(str).str.upper()
            print('Datahub query executed, {len(reports_dh)} records found')
            reports_dh.db.set_query(get_reports_by_id(report_id_table = '#TempReports'))
            reports_lsdb = reports_dh.db.execute(CONN_DICT[self.customer_info['DBLocation']], source_col = 'ReportId', temp_table_name = '#TempReports')
            reports_lsdb['ReportYear'] = pd.to_datetime(reports_lsdb['ReportDate']).dt.year
            reports_lsdb['ReportMonth'] = pd.to_datetime(reports_lsdb['ReportDate']).dt.month
            reports_lsdb['ReportWeek'] = pd.to_datetime(reports_lsdb['ReportDate']).dt.isocalendar().week
            print(f'LSDB query executed, {len(reports_lsdb)} records found')
            reports = pd.merge(reports_lsdb[LSDB_COLS], reports_dh[DATAHUB_COLS], on = 'ReportId', how = 'left')
            print(f'Reports merged, {len(reports)} records found')
                # Add/update the LastUpdated column to the reports DataFrame as current timestamp
            reports['LastUpdated'] = datetime.now()
            self.Logger.info(f"Reports from LSDB starting from {self.starting_date}: {len(reports)}")
            self.data['output'] = reports

    

if __name__ == "__main__":
    arguments = {'conn': KPIHub_Conn}
    ingester = ReportSummaryIngester(arguments)
    ingester.set_customer_info(ingester.customer_list.iloc[0])
    ingester.query_data()
    ingester.push_data()
    ingester.sanity_check()