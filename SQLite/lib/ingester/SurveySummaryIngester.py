from locallib.picarrodb import *
from locallib.slack import *
from locallib.etl import Loggers

import os
import sys
import pandas as pd
from datetime import datetime, date, timedelta
import geopandas as gpd
from shapely.geometry import Polygon, LineString, MultiLineString


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

class SurveySummaryIngesterDuplicates(Ingester):
    def __init__(self, arguments):
        super().__init__(arguments)
        self.table = KPI_SurveySummary

    def update_check(self):
        customer_name = self.customer_info['Name']
        customer_id = self.customer_info['CustomerId']
        customer_db = self.customer_info['DBLocation']

        self.Logger.info(f"Processing customer: {customer_name}")
        self.Logger.info(f"Getting reports from {self.update_window} to {self.current_date}")
        #Query the last report
        self.data['reports'] = Query(
            f"""
            SELECT ReportId, ReportDate, ReportArea, LastUpdated FROM KPI_ReportSummary
            WHERE CustomerId = '{self.customer_info['CustomerId']}'
            ORDER BY LastUpdated DESC
            """
        ).execute(KPIHub_Conn)

        self.data['survey_count'] = Query(
            f"""
            SELECT COUNT(*) as SurveyCount
            FROM KPI_SurveySummary
            WHERE ReportId IN (SELECT ReportId FROM KPI_ReportSummary WHERE CustomerId = '{customer_id}')
            """
        ).execute(KPIHub_Conn)

        if len(self.data['reports']) > 0:
            if (self.data['survey_count'].iloc[0]['SurveyCount']) > 0:
                self.check_flag = True
                self.starting_date = self.update_window
                self.Logger.info(f"Getting surveys from {self.update_window} to {self.current_date}")
                print(self.data['survey_count'].iloc[0]['SurveyCount'])

            else:
                self.Logger.info(f"No emissions found, processing from start")
                self.starting_date = STARTING_DATE
                self.check_flag = True
        else:
            self.Logger.info(f"No reports found, skipping")
            self.check_flag = False

    def query_data(self):
        if self.check_flag:
            # Ensure the ReportDate values are in datetime format before comparison,
            # handling both with and without microseconds (mixed formats)
            self.data['reports']['ReportDate'] = pd.to_datetime(self.data['reports']['ReportDate'], format='mixed')

            # Handle potential issues with type mismatch when comparing datetimes
            # Coerce both sides to date for a robust comparison
            reports_to_query = self.data['reports'][
                pd.to_datetime(self.data['reports']['ReportDate']).dt.date >= pd.to_datetime(self.starting_date).date()
            ]
            self.Logger.info(f"Reports to query: {len(reports_to_query)}")
            reports_to_query.db.set_query(query_surveys_table(report_table="#TempReports"))
            surveys = reports_to_query.db.execute(CONN_DICT[self.customer_info['DBLocation']], source_col = 'ReportId', temp_table_name = '#TempReports')
            surveys.db.set_query(query_segments_table(survey_table="#TempSurvey"))
            self.Logger.info(f"Surveys from LSDB: {len(surveys)}")
            segments = surveys.db.execute(CONN_DICT[self.customer_info['DBLocation']], source_col = 'SurveyId', temp_table_name = '#TempSurvey')
            self.Logger.info(f"Segments from LSDB: {len(segments)}")

            
            # Convert StartEpoch to datetime (time only, no date)
            segments['StartTime'] = pd.to_datetime(segments['StartEpoch'], unit='s').dt.time
            segments['StartDate'] = pd.to_datetime(segments['StartEpoch'], unit='s')
            segments['DayNight'] = segments['StartTime'].apply(lambda t: get_day_night(t, SUNRISE_TIME, SUNSET_TIME))
            segments['ActiveIdle'] = segments['CarSpeedMedian'].apply(lambda x: set_actie_idle(x, SPEED_THRESHOLD))

            # Set the starting time as a datetime object
            surveys['StartHour'] = pd.to_datetime(surveys['StartEpoch'], unit='s').dt.hour
            surveys['StartTime'] = pd.to_datetime(surveys['StartEpoch'], unit='s').dt.time
            surveys['EndHour'] = pd.to_datetime(surveys['EndEpoch'], unit='s').dt.hour
            surveys['EndTime'] = pd.to_datetime(surveys['EndEpoch'], unit='s').dt.time
            surveys['StartDay'] = pd.to_datetime(surveys['StartEpoch'], unit='s').dt.date
            surveys['EndDay'] = pd.to_datetime(surveys['EndEpoch'], unit='s').dt.date

            # Calculate the duration (in minutes) between StartEpoch and EndEpoch for each survey
            surveys['DurationMinutes'] = (
                surveys['EndEpoch'] - surveys['StartEpoch']
            ) / 60

            # Apply the function row-wise (axis=1) to build a DataFrame summary
            survey_summary = surveys.apply(survey_summary_apply, axis=1)
            segment_summary = segments.groupby("SurveyId").apply(segment_summary_apply)
            survey_summary = pd.merge(survey_summary,segment_summary,on="SurveyId",how="left")

            upload = survey_summary.reset_index(drop=True)
            upload.fillna(0, inplace=True)
            upload['LastUpdated'] = datetime.now()
            self.data['output'] = upload
        else:
            self.Logger.info(f"No reports found, skipping")
        
    def sanity_check(self):
        super().sanity_check()
        #Get all the reports from the KPI_SurveySummary table
        df_surveys = Query(query = f"SELECT DISTINCT ReportId FROM KPI_SurveySummary WHERE ReportId IN (SELECT ReportId FROM KPI_ReportSummary WHERE CustomerId = '{self.customer_info['CustomerId']}')").execute(KPIHub_Conn)
        self.Logger.info(f"Total number of unique reports from KPI_SurveySummary: {len(df_surveys)}")

    def push_data(self):
        super().push_data(primary_key = ['SurveyId','ReportId'])
        self.Logger.info(f"Data pushed to {db_path}")


#Updated class that handles the duplicates in Surveys on Report by working on the area table
class SurveySummaryIngester(Ingester):
    def __init__(self, arguments):
        super().__init__(arguments)
        self.table = KPI_SurveySummary

    def update_check(self):
        customer_name = self.customer_info['Name']
        customer_id = self.customer_info['CustomerId']
        customer_db = self.customer_info['DBLocation']
        self.Logger.info(f"Processing customer: {customer_name}")

        #Query the reports from KPI_EmissionSources
        query_kpi_survey_summary = f"""SELECT DISTINCT ReportId FROM KPI_SurveySummary WHERE ReportId IN (SELECT ReportId FROM KPI_ReportSummary WHERE CustomerId = '{self.customer_info['CustomerId']}')"""
        reports_kpi_survey_summary = Query(query = query_kpi_survey_summary).execute(KPIHub_Conn)
        num_reports_kpi_survey_summary = len(reports_kpi_survey_summary)

        #Query the reports from KPI_ReportSummary
        query_kpi_report = f"""SELECT ReportId FROM KPI_ReportSummary WHERE CustomerId = '{self.customer_info['CustomerId']}'"""
        reports_kpi_hub = Query(query = query_kpi_report).execute(KPIHub_Conn)
        num_reports_kpi_hub = len(reports_kpi_hub)

        #Check if there are new reports
        reports_into = reports_kpi_hub[~reports_kpi_hub['ReportId'].isin(reports_kpi_survey_summary['ReportId'])]
        reports_deleted = reports_kpi_survey_summary[~reports_kpi_survey_summary['ReportId'].isin(reports_kpi_hub['ReportId'])]

        self.data['reports_into'] = reports_into.copy()
        self.data['reports_deleted'] = reports_deleted.copy()
        self.data['num_reports_kpi_survey_summary'] = num_reports_kpi_survey_summary
        self.data['num_reports_kpi_hub'] = num_reports_kpi_hub

        if (num_reports_kpi_hub > 0):
            self.Logger.info(f"Number of reports in KPI_ReportSummary: {num_reports_kpi_hub}")
            if(num_reports_kpi_survey_summary == 0):
                #No reports in the KPI_EmissionSources
                self.Logger.info("No reports in KPIHub, starting from the beginning")
                self.check_flag = True
            else:
                #Reports in the KPIHub
                self.Logger.info(f"Number of reports in KPI_SurveySummary: {num_reports_kpi_survey_summary}")
                if len(reports_into) > 0 or len(reports_deleted) > 0:
                    self.Logger.info(f"Number of new reports into the KPI_SurveySummary: {len(reports_into)}")
                    self.Logger.info(f"Number of deleted reports in the KPI_ReportSummary: {len(reports_deleted)}")
                    self.check_flag = True
                else:
                    self.Logger.info("No new reports into the KPI_SurveySummary or deleted reports in the KPI_SurveySummary")
                    self.check_flag = False
        else:
            self.Logger.info("No reports in KPI_ReportSummary")
            self.check_flag = False

    def query_data(self):
        if self.check_flag and len(self.data['reports_into']) > 0:
            reports_into = self.data['reports_into'].copy()
            reports_into.db.set_query(get_reports(self.customer_info['Name'], starting_date=self.starting_date, report_id_table = '#TempReport', final_checkbox = True))
            reports_to_query = reports_into.db.execute(CONN_DICT[self.customer_info['DBLocation']], source_col = 'ReportId', temp_table_name = '#TempReport')
            reports_to_query.db.set_query(query_surveys_table(report_table="#TempReports"))
            surveys = reports_to_query.db.execute(CONN_DICT[self.customer_info['DBLocation']], source_col = 'ReportId', temp_table_name = '#TempReports')
            surveys.db.set_query(query_segments_table(survey_table="#TempSurvey"))
            self.Logger.info(f"Reports from KPI_ReportSummary: {len(reports_to_query)}")
            self.Logger.info(f"Surveys from LSDB: {len(surveys)}")
            if len(surveys) == 0:
                self.Logger.info(f"No surveys found, skipping")
                self.check_flag = False
                return
            segments = surveys.db.execute(CONN_DICT[self.customer_info['DBLocation']], source_col = 'SurveyId', temp_table_name = '#TempSurvey')
            self.Logger.info(f"Segments from LSDB: {len(segments)}")


            # Set the starting time as a datetime object
            surveys['StartHour'] = pd.to_datetime(surveys['StartEpoch'], unit='s').dt.hour
            surveys['StartTime'] = pd.to_datetime(surveys['StartEpoch'], unit='s').dt.time
            surveys['EndHour'] = pd.to_datetime(surveys['EndEpoch'], unit='s').dt.hour
            surveys['EndTime'] = pd.to_datetime(surveys['EndEpoch'], unit='s').dt.time
            surveys['StartDay'] = pd.to_datetime(surveys['StartEpoch'], unit='s').dt.date
            surveys['EndDay'] = pd.to_datetime(surveys['EndEpoch'], unit='s').dt.date

            # Calculate the duration (in minutes) between StartEpoch and EndEpoch for each survey
            surveys['DurationMinutes'] = (
                surveys['EndEpoch'] - surveys['StartEpoch']
            ) / 60      

            # Prepare the report_gdf for report area lookup
            reports_to_query["geometry"] = gpd.GeoSeries.from_wkt(reports_to_query["ReportArea"])

            report_gdf = gpd.GeoDataFrame(
                reports_to_query,
                geometry="geometry",
                crs="EPSG:4326"
            )
            utm_crs = report_gdf.estimate_utm_crs()
            report_gdf = report_gdf.to_crs(utm_crs)

            segments_gdf = gpd.GeoDataFrame(
                segments,
                geometry=gpd.GeoSeries.from_wkt(segments['Shape']),
                crs="EPSG:4326"
            )
            segments_gdf = segments_gdf.to_crs(utm_crs)
        
            survey_summary = surveys.apply(survey_summary_apply, axis=1)
            outputs =  []
            self.data['reports_gdf'] = report_gdf
            self.data['segments_gdf'] = segments_gdf
            self.data['survey_gdf'] = surveys
            for idx, row in report_gdf.iterrows():
                self.Logger.File.info(f"Processing report {row['ReportId']}, {idx+1} of {len(report_gdf)}")
                surveys_subset = surveys[surveys['ReportId'] == row['ReportId']]['SurveyId']
                segments_subset = segments_gdf[segments_gdf['SurveyId'].isin(surveys_subset)]
                segments_in_report = gpd.overlay(
                    segments_subset,
                    gpd.GeoDataFrame([row], geometry=[row['geometry']], crs=segments_subset.crs),
                    how='intersection',
                    keep_geom_type=False
                )

                if segments_in_report.empty:
                    continue  # skip if intersection is empty
                self.data['segments_in_report'] = segments_in_report
                # Convert StartEpoch to datetime (time only, no date)
                segments_in_report['StartTime'] = pd.to_datetime(segments_in_report['StartEpoch'], unit='s').dt.time
                segments_in_report['StartDate'] = pd.to_datetime(segments_in_report['StartEpoch'], unit='s')
                segments_in_report['DayNight'] = segments_in_report['StartTime'].apply(lambda t: get_day_night(t, SUNRISE_TIME, SUNSET_TIME))
                segments_in_report['ActiveIdle'] = segments_in_report['CarSpeedMedian'].apply(lambda x: set_actie_idle(x, SPEED_THRESHOLD))

                # Group by SurveyId and calculate the aggregated metrics per SurveyId (for surveys associated with this report)
                segment_grouped = segments_in_report.groupby('SurveyId')

                for survey_id, group in segment_grouped:
                    output = {
                        'SurveyId': survey_id,
                        'ReportId': row['ReportId'],
                        'DaySegments': (group['DayNight'] == 'Day').sum(),
                        'NightSegments': (group['DayNight'] == 'Night').sum(),
                        'ActiveSegments': (group['ActiveIdle'] == 'Active').sum(),
                        'IdleSegments': (group['ActiveIdle'] == 'Idle').sum(),
                        'TotalSegments': len(group),
                        'TotalKilometers': group['LengthMeters'].sum() / 1000,
                        'DayKilometers': group.loc[group['DayNight'] == 'Day', 'LengthMeters'].sum() / 1000,
                        'NightKilometers': group.loc[group['DayNight'] == 'Night', 'LengthMeters'].sum() / 1000,
                        'SegmentDurationMinutes': group['DurationSeconds'].sum() / 60,
                        'IdleTimeMinutes': group.loc[group['ActiveIdle'] == 'Idle', 'DurationSeconds'].sum() / 60,
                        'ActiveTimeMinutes': group.loc[group['ActiveIdle'] == 'Active', 'DurationSeconds'].sum() / 60,
                        'AvgSpeedKm': 3.6 * group['CarSpeedMedian'].mean(),
                    }
                    outputs.append(output)
       

            if not outputs:
                self.Logger.info("No segment intersections found for any report, skipping")
                self.check_flag = False
                return

            output_df = pd.DataFrame(outputs)
            merged_df = pd.merge(
                survey_summary,
                output_df,
                left_on=["SurveyId", "ReportId"],
                right_on=["SurveyId", "ReportId"],
                how="inner"
            )
            merged_df['SegmentWeight'] = merged_df['TotalSegments'] / merged_df['TotalSegmentsInSurvey']
            merged_df['SurveyDurationMinutes'] = merged_df['SurveyRawDurationMinutes'] * merged_df['SegmentWeight']
            self.data['output'] = merged_df
            self.data['output']['LastUpdated'] = datetime.now()
        
        
    def sanity_check(self):
        super().sanity_check()
        #Get all the reports from the KPI_SurveySummary table
        df_surveys = Query(query = f"SELECT DISTINCT ReportId FROM KPI_SurveySummary WHERE ReportId IN (SELECT ReportId FROM KPI_ReportSummary WHERE CustomerId = '{self.customer_info['CustomerId']}')").execute(KPIHub_Conn)
        self.Logger.info(f"Total number of unique reports from KPI_SurveySummary: {len(df_surveys)}")

    def push_data(self):
        if self.check_flag and len(self.data['output']) > 0:
            super().push_data(primary_key = ['SurveyId','ReportId'])
            self.Logger.info(f"Data pushed to {db_path}")
        else:
            self.Logger.info(f"No data to push")


# Define a function to determine if survey is in 'day' or 'night'
def get_day_night(start_time, sunrise, sunset):
    # start_time should be a datetime.time object
    hour = start_time.hour
    if sunrise <= hour < sunset:
        return 'Day'
    else:
        return 'Night'

def set_actie_idle(speed, speed_threshold):
    if speed < speed_threshold:
        return 'Idle'
    else:
        return 'Active'

def segment_summary_apply(df):
    return pd.Series({
        'DaySegments': (df['DayNight'] == 'Day').sum(),
        'NightSegments': (df['DayNight'] == 'Night').sum(),
        'ActiveSegments': (df['ActiveIdle'] == 'Active').sum(),
        'IdleSegments': (df['ActiveIdle'] == 'Idle').sum(),
        'TotalSegments': len(df),
        'TotalKilometers': df['LengthMeters'].sum() / 1000,
        'DayKilometers': df.loc[df['DayNight'] == 'Day', 'LengthMeters'].sum() / 1000,
        'NightKilometers': df.loc[df['DayNight'] == 'Night', 'LengthMeters'].sum() / 1000,
        'SegmentDurationMinutes': df['DurationSeconds'].sum() / 60,
        'IdleTimeMinutes': df.loc[df['ActiveIdle'] == 'Idle', 'DurationSeconds'].sum() / 60,
        'ActiveTimeMinutes': df.loc[df['ActiveIdle'] == 'Active', 'DurationSeconds'].sum() / 60,
        'AvgSpeedKm': 3.6*df['CarSpeedMedian'].mean()

    })

def survey_summary_apply(row):
    return pd.Series({
        'SurveyId': row['SurveyId'],
        'SurveyorUnit': row['SurveyorUnit'],
        'SurveyRawDurationMinutes': row['DurationMinutes'],
        'ReportId': row['ReportId'],
        'StartHour': row['StartHour'],
        'StartTime': row['StartTime'],
        'StartEpoch': row['StartEpoch'],
        'EndTime': row['EndTime'],
        'EndEpoch': row['EndEpoch'],
        'StartDay': row['StartDay'],
        'EndDay': row['EndDay'],
        'LateralRotation': row['LateralRotation'],
        'NumberOfPeaks': row['NumberOfPeaks'],
        'TotalSegmentsInSurvey': row['TotalSegmentsInSurvey']
    })
