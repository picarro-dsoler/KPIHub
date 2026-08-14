"""Populate kpihub MV_SurveySummary_* tables using SurveySummaryIngester logic."""
from __future__ import annotations

import os
import sys
import uuid

import pandas as pd
from sqlalchemy import text

directory = os.path.abspath(os.path.join(os.path.dirname(__file__), "ingester"))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))
sys.path.append(directory)

from config import CONN_DICT, STARTING_DATE
from ingester.SurveySummaryIngester import SurveySummaryIngester
from locallib.picarrodb import Query

MV_SURVEY_COLUMNS = [
  "SurveyId",
  "ReportId",
  "SurveyorUnit",
  "SurveyDurationMinutes",
  "SurveyRawDurationMinutes",
  "SegmentWeight",
  "StartHour",
  "StartTime",
  "StartEpoch",
  "EndTime",
  "EndEpoch",
  "StartDay",
  "EndDay",
  "LateralRotation",
  "NumberOfPeaks",
  "DaySegments",
  "NightSegments",
  "ActiveSegments",
  "IdleSegments",
  "TotalSegments",
  "TotalSegmentsInSurvey",
  "TotalKilometers",
  "DayKilometers",
  "NightKilometers",
  "IdleTimeMinutes",
  "ActiveTimeMinutes",
  "SegmentDurationMinutes",
  "AvgSpeedKm",
  "LastUpdated",
]


def mv_report_table(db_location: str) -> str:
  return f"MV_ReportSummary_{db_location.lower()}"


def mv_survey_table(db_location: str) -> str:
  return f"MV_SurveySummary_{db_location.lower()}"


def fetch_report_areas(report_ids: list, db_location: str, chunk_size: int = 200) -> pd.DataFrame:
  if not report_ids:
    return pd.DataFrame(columns=["ReportId", "ReportArea"])

  frames: list[pd.DataFrame] = []
  for offset in range(0, len(report_ids), chunk_size):
    chunk = report_ids[offset : offset + chunk_size]
    ids_sql = "', '".join(str(report_id) for report_id in chunk)
    query = f"""
      SELECT RA.ReportId, RA.Shape AS ReportArea
      FROM ReportArea RA
      WHERE RA.ReportId IN ('{ids_sql}')
    """
    frames.append(Query(query=query).execute(CONN_DICT[db_location]))

  if not frames:
    return pd.DataFrame(columns=["ReportId", "ReportArea"])
  return pd.concat(frames, ignore_index=True)


def prepare_survey_output(df: pd.DataFrame) -> pd.DataFrame:
  if df.empty:
    return df

  output = df.copy()
  output["StartTime"] = pd.to_datetime(output["StartEpoch"], unit="s")
  output["EndTime"] = pd.to_datetime(output["EndEpoch"], unit="s")
  output["LastUpdated"] = pd.to_datetime(output["LastUpdated"])

  int_cols = [
    "StartHour",
    "NumberOfPeaks",
    "DaySegments",
    "NightSegments",
    "ActiveSegments",
    "IdleSegments",
    "TotalSegments",
    "TotalSegmentsInSurvey",
  ]
  for col in int_cols:
    if col in output.columns:
      output[col] = output[col].fillna(0).astype(int)

  return output[MV_SURVEY_COLUMNS]


class SurveySummaryPostGISIngester(SurveySummaryIngester):
  def __init__(self, arguments):
    super().__init__(arguments)
    self.postgis_conn = arguments["postgis_conn"]

  def update_check(self):
    customer_name = self.customer_info["Name"]
    customer_id = self.customer_info["CustomerId"]
    db_location = self.customer_info["DBLocation"]
    report_table = mv_report_table(db_location)
    survey_table = mv_survey_table(db_location)

    self.Logger.info(f"Processing customer: {customer_name}")
    self.Logger.info(f"Getting reports from {self.update_window} to {self.current_date}")

    self.data["reports"] = Query(
      f"""
      SELECT "ReportId", "ReportDate", "LastUpdated"
      FROM kpihub."{report_table}"
      WHERE "CustomerId" = '{customer_id}'
      ORDER BY "LastUpdated" DESC
      """
    ).execute(self.postgis_conn)

    self.data["survey_count"] = Query(
      f"""
      SELECT COUNT(*) AS SurveyCount
      FROM kpihub."{survey_table}" ss
      WHERE ss."ReportId" IN (
        SELECT "ReportId"
        FROM kpihub."{report_table}"
        WHERE "CustomerId" = '{customer_id}'
      )
      """
    ).execute(self.postgis_conn)

    if len(self.data["reports"]) > 0:
      if self.data["survey_count"].iloc[0]["SurveyCount"] > 0:
        self.check_flag = True
        self.starting_date = self.update_window
        self.Logger.info(
          f"Existing survey rows found, processing from {self.update_window}"
        )
      else:
        self.Logger.info("No survey rows found, processing from start")
        self.starting_date = STARTING_DATE
        self.check_flag = True
    else:
      self.Logger.info("No reports found in PostGIS MV, skipping")
      self.check_flag = False

  def query_data(self):
    if not self.check_flag:
      self.Logger.info("No reports found, skipping")
      return

    report_ids = self.data["reports"]["ReportId"].astype(str).tolist()
    areas = fetch_report_areas(report_ids, self.customer_info["DBLocation"])
    self.data["reports"] = self.data["reports"].merge(areas, on="ReportId", how="left")
    self.data["reports"]["ReportArea"] = self.data["reports"]["ReportArea"].fillna(
      "POLYGON EMPTY"
    )

    super().query_data()

  def push_data(self, primary_key=None):
    if not self.check_flag or "output" not in self.data or self.data["output"].empty:
      self.Logger.info("No data to push")
      return

    db_location = self.customer_info["DBLocation"]
    customer_id = self.customer_info["CustomerId"]
    report_table = mv_report_table(db_location)
    survey_table = mv_survey_table(db_location)
    output = prepare_survey_output(self.data["output"])

    delete_sql = text(
      f"""
      DELETE FROM kpihub."{survey_table}"
      WHERE "ReportId" IN (
        SELECT "ReportId"
        FROM kpihub."{report_table}"
        WHERE "CustomerId" = :customer_id
      )
      """
    )

    insert_sql = text(
      f"""
      INSERT INTO kpihub."{survey_table}" (
        "SurveyId", "ReportId", "SurveyorUnit", "SurveyDurationMinutes",
        "SurveyRawDurationMinutes", "SegmentWeight", "StartHour", "StartTime",
        "StartEpoch", "EndTime", "EndEpoch", "StartDay", "EndDay",
        "LateralRotation", "NumberOfPeaks", "DaySegments", "NightSegments",
        "ActiveSegments", "IdleSegments", "TotalSegments", "TotalSegmentsInSurvey",
        "TotalKilometers", "DayKilometers", "NightKilometers", "IdleTimeMinutes",
        "ActiveTimeMinutes", "SegmentDurationMinutes", "AvgSpeedKm", "LastUpdated"
      ) VALUES (
        :SurveyId, :ReportId, :SurveyorUnit, :SurveyDurationMinutes,
        :SurveyRawDurationMinutes, :SegmentWeight, :StartHour, :StartTime,
        :StartEpoch, :EndTime, :EndEpoch, :StartDay, :EndDay,
        :LateralRotation, :NumberOfPeaks, :DaySegments, :NightSegments,
        :ActiveSegments, :IdleSegments, :TotalSegments, :TotalSegmentsInSurvey,
        :TotalKilometers, :DayKilometers, :NightKilometers, :IdleTimeMinutes,
        :ActiveTimeMinutes, :SegmentDurationMinutes, :AvgSpeedKm, :LastUpdated
      )
      ON CONFLICT ("SurveyId", "ReportId") DO UPDATE SET
        "SurveyorUnit" = EXCLUDED."SurveyorUnit",
        "SurveyDurationMinutes" = EXCLUDED."SurveyDurationMinutes",
        "SurveyRawDurationMinutes" = EXCLUDED."SurveyRawDurationMinutes",
        "SegmentWeight" = EXCLUDED."SegmentWeight",
        "StartHour" = EXCLUDED."StartHour",
        "StartTime" = EXCLUDED."StartTime",
        "StartEpoch" = EXCLUDED."StartEpoch",
        "EndTime" = EXCLUDED."EndTime",
        "EndEpoch" = EXCLUDED."EndEpoch",
        "StartDay" = EXCLUDED."StartDay",
        "EndDay" = EXCLUDED."EndDay",
        "LateralRotation" = EXCLUDED."LateralRotation",
        "NumberOfPeaks" = EXCLUDED."NumberOfPeaks",
        "DaySegments" = EXCLUDED."DaySegments",
        "NightSegments" = EXCLUDED."NightSegments",
        "ActiveSegments" = EXCLUDED."ActiveSegments",
        "IdleSegments" = EXCLUDED."IdleSegments",
        "TotalSegments" = EXCLUDED."TotalSegments",
        "TotalSegmentsInSurvey" = EXCLUDED."TotalSegmentsInSurvey",
        "TotalKilometers" = EXCLUDED."TotalKilometers",
        "DayKilometers" = EXCLUDED."DayKilometers",
        "NightKilometers" = EXCLUDED."NightKilometers",
        "IdleTimeMinutes" = EXCLUDED."IdleTimeMinutes",
        "ActiveTimeMinutes" = EXCLUDED."ActiveTimeMinutes",
        "SegmentDurationMinutes" = EXCLUDED."SegmentDurationMinutes",
        "AvgSpeedKm" = EXCLUDED."AvgSpeedKm",
        "LastUpdated" = EXCLUDED."LastUpdated"
      """
    )

    rows = []
    for _, row in output.iterrows():
      payload = row.to_dict()
      for key, value in payload.items():
        if pd.isna(value):
          payload[key] = None
        elif key in {"SurveyId", "ReportId"}:
          payload[key] = uuid.UUID(str(value))
        elif key in {"StartDay", "EndDay"} and value is not None:
          payload[key] = pd.to_datetime(value).date()
      rows.append(payload)

    with self.postgis_conn.engine.begin() as connection:
      connection.execute(delete_sql, {"customer_id": str(customer_id)})
      connection.execute(insert_sql, rows)

    self.Logger.info(
      f'Pushed {len(rows)} survey rows to kpihub."{survey_table}" for {customer_id}'
    )

  def sanity_check(self):
    db_location = self.customer_info["DBLocation"]
    report_table = mv_report_table(db_location)
    survey_table = mv_survey_table(db_location)
    customer_id = self.customer_info["CustomerId"]

    df_surveys = Query(
      f"""
      SELECT DISTINCT ss."ReportId"
      FROM kpihub."{survey_table}" ss
      WHERE ss."ReportId" IN (
        SELECT "ReportId"
        FROM kpihub."{report_table}"
        WHERE "CustomerId" = '{customer_id}'
      )
      """
    ).execute(self.postgis_conn)
    self.Logger.info(
      f'Total unique reports in kpihub."{survey_table}": {len(df_surveys)}'
    )
