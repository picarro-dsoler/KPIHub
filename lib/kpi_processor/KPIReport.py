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

from datetime import date
from datetime import timedelta
from functools import reduce
class KPISummary:
    def __init__(self, customer_name, aggregator = {}, period_dict = {'Week': 'ReportWeek'}):
        self.name = 'KPISummary'
        self.base_time = {'Year': 'ReportYear'}
        self.period_dict = period_dict
        self.data = {}
        self.tableList = []
        self.aggregator_dict = {**self.base_time, **aggregator, **period_dict}
        self.aggregator = list(self.aggregator_dict.values())
        self.customer_name = customer_name

        self.customer_id = None
        result = Query(query = f"SELECT CustomerId FROM KPI_Customer WHERE Name = '{self.customer_name}'").execute([KPIHub_Conn])
        if not result.empty:
            self.customer_id = result.iloc[0]['CustomerId']
        else:
            raise ValueError(f"Customer name '{self.customer_name}' not found in KPI_Customer table.")
   
    
    def query_table(self):
        for table in self.tableList:
            self.data[table] = Query(query = f"SELECT * FROM {table.name} WHERE ReportId IN (SELECT ReportId FROM KPI_ReportSummary WHERE CustomerId IN (SELECT CustomerId FROM KPI_Customer WHERE Name = '{self.customer_name}'))").execute([KPIHub_Conn])

    def process_data(self, on='ReportId'):
        # Aggregate and operate
        if not self.tableList:
            self.data['output'] = pd.DataFrame()
        elif len(self.tableList) == 1:
            temp_data = self.data[self.tableList[0]]
        else:
            temp_data = self.data[self.tableList[0]]
            for table in self.tableList[1:]:
                temp_data = pd.merge(temp_data, self.data[table], on=on, how='inner')
        if self.tableList:
            self.data['output'] = temp_data.groupby(self.aggregator).apply(self.processor)
            self.data['output'] = self.data['output'].round(2)
 
        self.melter()


    def push_data(self, PrimaryKey = 'Id'):
        # Fix db path to go from the root directory to database/KPIHub.db
        db_path = '/home/sandbox/personal-repos/KPIHub/database/KPIHub_Dev.db'
        KPI_Data.update_table(arguments = {'DataFrame': self.data['output'], 'db_path': db_path, 'PrimaryKey': PrimaryKey})
 
    def processor(self, df):
        return df

    def melter(self):
        r = self.data['output'].reset_index()
        r_long = r.melt(id_vars=self.aggregator, var_name='KPIId', value_name='Value')
        r_long['Id'] = r_long.apply(self.generate_id, axis=1)
        period_dict_values = list(self.period_dict.values())
        period_dict_keys = list(self.period_dict.keys())
        base_time_values = list(self.base_time.values())
        base_time_keys = list(self.base_time.keys())
        if len(period_dict_values) > 0:
            r_long = r_long.rename(columns={period_dict_values[0]: 'PeriodValue', base_time_values[0]: 'Year'})
            r_long['PeriodType'] = period_dict_keys[0]
        else:
            r_long = r_long.rename(columns={base_time_values[0]: base_time_keys[0]})
            r_long['PeriodType'] = base_time_keys[0]
    
        r_long['LastUpdated'] = datetime.now()
        r_long['CustomerId'] = self.customer_id

        self.data['output'] = r_long


    def generate_id(self, row):
        output = f"{row['KPIId']}_{self.customer_name}"
        for key, value in self.aggregator_dict.items():
            if isinstance(row[value], str):
                output = f"{output}_{key[0]}{row[value].replace(' ', '')}"
            else:
                output = f"{output}_{key[0]}{row[value]}"
           

        return output

class KPIPOR(KPISummary):
    def __init__(self, customer_name, aggregator = {}, period_dict = {'Week': 'ReportWeek'}):
        super().__init__(customer_name, aggregator, period_dict)
        self.tableList = [KPI_ReportSummary]
        self.name = 'KPIPOR'
    
    def process_data(self, on='ReportId'):
        PORData = Query(query = f"SELECT * FROM KPI_POR WHERE CustomerId = '{self.customer_id}'").execute(KPIHub_Conn)
        PORValue = PORData['Value'].values[0]
        # Attach POR value to agg_df as a new column named 'POR'
        if PORValue == 0:
            raise ValueError(f"POR not found for {self.customer_name}")
        else:
            reports = self.data[KPI_ReportSummary]
            # -- Fix: Filter reports that are within ANY PORData period, accounting for multiple periods --
            mask = reports.apply(
                lambda row: any(
                    pd.to_datetime(row['ReportDate']) >= pd.to_datetime(por_row['StartingDate']) and
                    pd.to_datetime(row['ReportDate']) <= pd.to_datetime(por_row['EndingDate'])
                    for _, por_row in PORData.iterrows()
                ),
                axis=1
            )
            PORReports = reports[mask]
            report_years = []
            report_weeks = []
            values = []

            for _, row in PORData.iterrows():
                value = row['Value']
                start_date = pd.to_datetime(row['StartingDate'])
                end_date = pd.to_datetime(row['EndingDate'])

                start_year = start_date.year
                end_year = end_date.year

                for year in range(start_year, end_year + 1):
                    if year == start_year:
                        first_week_date = start_date
                    else:
                        first_week_date = pd.to_datetime(f"{year}-01-01")

                    if year == end_year:
                        last_week_date = end_date
                    else:
                        last_week_date = pd.to_datetime(f"{year}-12-31")

                    week_date = first_week_date
                    week_date = week_date - pd.Timedelta(days=week_date.weekday())  # previous Monday

                    while week_date <= last_week_date:
                        iso_calendar = week_date.isocalendar()
                        week_number = iso_calendar.week
                        year_number = iso_calendar.year
                        if year_number == year:
                            report_years.append(year)
                            report_weeks.append(week_number)
                            values.append(value)
                        week_date = week_date + pd.Timedelta(weeks=1)

                por_summary_df = pd.DataFrame({
                    'ReportYear': report_years,
                    'ReportWeek': report_weeks,
                    'POR': values
                }).set_index(['ReportYear', 'ReportWeek'])

                # Perform the aggregation and assign to a new DataFrame to avoid SettingWithCopyWarning
            agg_df = PORReports.groupby(self.aggregator).agg({
                'AssetCoveredLengthKm': 'sum',
            })

            agg_df['CumulativeAssetCoveredLengthKm'] = agg_df.groupby('ReportYear')['AssetCoveredLengthKm'].cumsum()

            agg_df = agg_df.join(por_summary_df, how="left")
            agg_df['CurrentCompletion'] = agg_df['CumulativeAssetCoveredLengthKm'] / agg_df['POR']
            agg_df['CurrentCompletion'] = (100*(agg_df['CurrentCompletion'])).round(2)
            agg_df.drop(columns=['AssetCoveredLengthKm'], inplace=True)
            self.data['output'] = agg_df

            self.melter()


class KPIPeakSAT(KPISummary):
    def __init__(self, customer_name, aggregator = {}, period_dict = {'Week': 'WeekNumber'}):
        super().__init__(customer_name, aggregator, period_dict)
        self.tableList = [KPI_PeakAboveSAT]
        self.name = 'KPIPeakSAT'
    def query_table(self):
        for table in self.tableList:
            self.data[table] = Query(query = f"SELECT * FROM {table.name} WHERE CustomerId IN (SELECT CustomerId FROM KPI_Customer WHERE Name = '{self.customer_name}')").execute([KPIHub_Conn])

    def processor(self, df):
        return pd.Series({
            'PeakAboveSATCount': df['PeakId'].count()
       
        })

class KPIReport(KPISummary):
    def __init__(self, customer_name, aggregator = {}, period_dict = {'Week': 'ReportWeek'}):
        super().__init__(customer_name, aggregator, period_dict)
        self.tableList = [KPI_ReportSummary]
        self.name = 'KPIReport'
    def processor(self, df):
        out = {
            'FOVMain': 100*df['DistributionPipeCoveredKm'].sum()/df['DistributionPipeKm'].sum(),
            'ReportAssetLengthKm': df['ReportAssetLengthKm'].sum() if 'ReportAssetLengthKm' in df else None,
            'AssetCoveredLengthKm': df['AssetCoveredLengthKm'].sum() if 'AssetCoveredLengthKm' in df else None,
            'DistributionPipeKm': df['DistributionPipeKm'].sum() if 'DistributionPipeKm' in df else None,
            'DistributionPipeCoveredKm': df['DistributionPipeCoveredKm'].sum() if 'DistributionPipeCoveredKm' in df else None,
            'ServicePipeKm': df['ServicePipeKm'].sum() if 'ServicePipeKm' in df else None,
            'ServicePipeCoveredKm': df['ServicePipeCoveredKm'].sum() if 'ServicePipeCoveredKm' in df else None,
            'ReportCount': df.shape[0]}
            
        return pd.Series(out)

class KPIEmissionSource(KPISummary):
    def __init__(self, customer_name, aggregator = {}, period_dict = {'Week': 'ReportWeek'}):
        super().__init__(customer_name, aggregator, period_dict)
        self.tableList = [KPI_ReportSummary,KPI_EmissionSourceSummary]
        self.name = 'KPIEmissionSource'
    def processor(self, df):
        denominator = 'DistributionPipeCoveredKm'
        out = {}
        denom = df[denominator].sum()
        lisa_count = df["LisaCount"].sum()
        out["LisaCount"] = lisa_count
        out["EmissionRate"] = df["EmissionRate"].sum()
        out["B0Count"] = df["B0Count"].sum()
        out["B1Count"] = df["B1Count"].sum()
        out["Bm1Count"] = df["Bm1Count"].sum()
        out["Bm2Count"] = df["Bm2Count"].sum()
        out["NGCount"] = df["NGCount"].sum()
        out["PGCount"] = df["PGCount"].sum()
        out["Not_NGCount"] = df["Not_NGCount"].sum()

        out["EmissionRateLPM"] = df["EmissionRateLPM"].sum()
        out["RepresentativeEmissionRate"] = df["RepresentativeEmissionRate"].sum()
        out["RepresentativeEmissionRateLPM"] = df["RepresentativeEmissionRateLPM"].sum()
        out["B0RepEmissionRateLPM"] = df["B0RepEmissionRateLPM"].sum()
        out["B1RepEmissionRateLPM"] = df["B1RepEmissionRateLPM"].sum()
        out["Bm1RepEmissionRateLPM"] = df["Bm1RepEmissionRateLPM"].sum()
        out["Bm2RepEmissionRateLPM"] = df["Bm2RepEmissionRateLPM"].sum()
        out["B0RepEmissionRate"] = df["B0RepEmissionRate"].sum()
        out["B1RepEmissionRate"] = df["B1RepEmissionRate"].sum()
        out["Bm1RepEmissionRate"] = df["Bm1RepEmissionRate"].sum()
        out["Bm2RepEmissionRate"] = df["Bm2RepEmissionRate"].sum()

        out["LisaDensity"] = lisa_count / denom if denom else None
        out["InstatanoeusEmission"] = out["EmissionRate"] / denom if denom else None
        out["InstatanoeusEmissionLPM"] = out["EmissionRateLPM"] / denom if denom else None
        out["InstatanoeusRepEmission"] = out["RepresentativeEmissionRate"] / denom if denom else None
        out["InstatanoeusRepEmissionLPM"] = out["RepresentativeEmissionRateLPM"] / denom if denom else None
        out["B0Density"] = out["B0Count"] / denom if denom else None
        out["B1Density"] = out["B1Count"] / denom if denom else None
        out["Bm1Density"] = out["Bm1Count"] / denom if denom else None
        out["Bm2Density"] = out["Bm2Count"] / denom if denom else None
        out["NGDensity"] = out["NGCount"] / denom if denom else None
        out["PGDensity"] = out["PGCount"] / denom if denom else None

        total_sum = out['NGCount'] + out['Not_NGCount'] + out['PGCount']

        out["B0Share"] = 100*out["B0Count"] / lisa_count if lisa_count else None
        out["B1Share"] = 100*out["B1Count"] / lisa_count if lisa_count else None
        out["Bm1Share"] = 100*out["Bm1Count"] / lisa_count if lisa_count else None
        out["Bm2Share"] = 100*out["Bm2Count"] / lisa_count if lisa_count else None
        out["NGShare"] = 100*out["NGCount"] / total_sum if total_sum else None
        out["PGShare"] = 100*out["PGCount"] / total_sum if total_sum else None
        out["Not_NGShare"] = 100*out["Not_NGCount"] / total_sum if total_sum else None
        return pd.Series(out)

class KPISurveySummary(KPISummary):
    def __init__(self, customer_name, aggregator = {}, period_dict = {'Week': 'ReportWeek'}):
        super().__init__(customer_name, aggregator, period_dict)
        self.tableList = [KPI_ReportSummary,KPI_SurveySummary]
        self.name = 'KPISurveySummary'
    def query_table(self):
        super().query_table()
        self.data['KPI_Utilization'] = Query(query = f"SELECT * FROM KPI_Utilization WHERE CustomerId = '{self.customer_id}'").execute(KPIHub_Conn)

    def processor(self, df):
        # Empty period_dict => yearly KPI; skip week-dependent utilization metrics
        is_yearly = not self.period_dict

        unique_reports = df.drop_duplicates(subset=['ReportId'])
        no_surveyors = df['SurveyorUnit'].nunique()
        surveyDurationHours = df['SurveyDurationMinutes'].sum()/60
        starndardTargetTimeHours = 6*5*no_surveyors
        surveyCount = df['SurveyId'].nunique()
        avg_speed_weighted = df['AvgSpeedKm'] * df['TotalSegments']

        result = {
            'SurveyDurationHours': surveyDurationHours,
            'StarndardUtilization': 100*surveyDurationHours/starndardTargetTimeHours,
            'TotalSurveyors': no_surveyors,
            'ProductivityPerSurveyor': unique_reports['DistributionPipeCoveredKm'].sum()/no_surveyors,
            'SurveyCount': surveyCount,
            'AvgSpeedKm': avg_speed_weighted.sum()/df['TotalSegments'].sum(),
            'IdleTime': 100*df['IdleTimeMinutes'].sum()/df['SurveyDurationMinutes'].sum(),
            'TotalDrivenLengthKm': df['TotalKilometers'].sum(),
            'DrivingRatio': df['TotalKilometers'].sum()/unique_reports['AssetCoveredLengthKm'].sum(),
            'NightDrivenLength': df['NightKilometers'].sum(),
            'DayDrivenLength': df['DayKilometers'].sum(),
            'NightRatio': 100*df['NightKilometers'].sum()/df['TotalKilometers'].sum(),
            'DayRatio': 100*df['DayKilometers'].sum()/df['TotalKilometers'].sum(),
        }

        if not is_yearly:
            hours = self.data['KPI_Utilization']['WorkingHours'].values[0]
            days = self.data['KPI_Utilization']['WorkingDays'].values[0]
            if hasattr(df, 'name') and df.name is not None:
                group_keys = (df.name,) if not isinstance(df.name, tuple) else df.name
                name_map = dict(zip(self.aggregator, group_keys))
                group_year = name_map.get('ReportYear')
                group_week_range = name_map.get('ReportWeek')
            else:
                group_year, group_week_range = None, None

            if group_year is not None and group_week_range is not None:
                day_count = days_in_week_range(group_week_range, group_year, days)
            else:
                day_count = None

            targetTimeHours = day_count*hours*no_surveyors
            result.update({
                'TargetDurationHours': targetTimeHours,
                'CustomerUtilization': 100*surveyDurationHours/targetTimeHours,
                'SurveysCarDay': surveyCount/no_surveyors/day_count,
                'DaysCount': day_count,
            })

        return pd.Series(result)


def days_in_week_range(week_number, year, max_days = 7):
    """
    Helper to count days in a week. If it's the current week, return days up to today.
    week_number: int week number (ISO, 1-53).
    year: int year.
    current_week: int, current week number.
    """

    # Get Monday of the ISO week
    try:
        start_date = date.fromisocalendar(int(year), int(week_number), 1)
    except Exception:
        # If not a valid ISO week/year, fall back to 7
        return max_days

    # End on Sunday
    end_date = start_date + timedelta(days=6)

    today = datetime.now().date()
    this_iso = today.isocalendar()[:2]  # (year, week)

    if (int(year), int(week_number)) == this_iso:
        delta = (today - start_date).days + 1  # include today
        return min(max(delta, 0), 7)
    else:
        return max_days