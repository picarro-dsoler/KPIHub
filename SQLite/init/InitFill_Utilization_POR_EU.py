import os
import sys

init_directory = os.path.abspath(os.path.dirname(__file__))
_root = os.path.abspath(os.path.join(init_directory, ".."))

# Add KPIHub root to sys.path so `lib.*` imports resolve regardless of cwd.
sys.path.insert(0, _root)
os.chdir(_root)

import pandas as pd

from locallib.picarrodb import *
from locallib.query import *

from lib.tables.IngesterTables import *
from lib.handlers.CustomerHandler import *
from lib.config import *
from lib.KPIHubConnection import *

customer_info_path = os.path.join(init_directory, "CustomerInfo.csv")
customer_info_df = pd.read_csv(customer_info_path)
customers = KPI_Customer.query_table({"db_path": DB_PATH})

# Default utilization for every customer in KPI_Customer
for _, customer in customers.iterrows():
    add_customer_utilization(customer["Name"])

# Overwrite with CustomerInfo.csv where values are provided
for _, customer in customer_info_df.iterrows():
    print(customer["CustomerName"])
    base_surveyors = int(customer["BaseSurveyors"]) if pd.notna(customer["BaseSurveyors"]) else 0
    sunrise_hour = int(customer["SunriseHour"]) if pd.notna(customer["SunriseHour"]) else SUNRISE_TIME
    sunset_hour = int(customer["SunsetHour"]) if pd.notna(customer["SunsetHour"]) else SUNSET_TIME

    add_customer_utilization(
        customer["CustomerName"],
        working_hours=int(customer["WorkingHours"]),
        working_days=int(customer["WorkingDays"]),
        base_surveyor_count=base_surveyors,
        sunrise_hour=sunrise_hour,
        sunset_hour=sunset_hour,
    )

    current_year = datetime.now().year
    default_por_start_date = f"01-01-{current_year}"
    default_por_end_date = f"31-12-{current_year}"
    por_year = int(customer["PORYear"]) if pd.notna(customer["PORYear"]) else current_year

    add_por(
        customer_name=customer["CustomerName"],
        year=por_year,
        value=customer["POR"] if pd.notna(customer["POR"]) else 0,
        StartingDate=customer["PORStartingDate"] if pd.notna(customer["PORStartingDate"]) else default_por_start_date,
        EndingDate=customer["POREndingDate"] if pd.notna(customer["POREndingDate"]) else default_por_end_date,
        Description="",
    )
    print("POR added")

    add_output_excel_location(
        customer["CustomerName"],
        customer["OutputExcelFolder"],
        KPIHub_Conn,
    )
    print("Output Excel Location added")

print(f"Updated utilization, POR, and output folders for {len(customer_info_df)} customers in {DB_PATH}")
