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

class SurveySummaryIngester(Ingester):
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
            SELECT ReportId, ReportDate, LastUpdated FROM KPI_ReportSummary
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
                self.Logger.info(f"Getting emissions from {self.update_window} to {self.current_date}")

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
        'SurveyDurationMinutes': row['DurationMinutes'],
        'ReportId': row['ReportId'],
        'StartHour': row['StartHour'],
        'StartTime': row['StartTime'],
        'StartEpoch': row['StartEpoch'],
        'EndTime': row['EndTime'],
        'EndEpoch': row['EndEpoch'],
        'StartDay': row['StartDay'],
        'EndDay': row['EndDay'],
        'LateralRotation': row['LateralRotation'],
        'NumberOfPeaks': row['NumberOfPeaks']
    })