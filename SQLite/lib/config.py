import sqlite3
from locallib.picarrodb import *
from datetime import date
#DB_PATH = 'database/KPIHub_Dev.db'
DB_PATH = 'database/KPIHub_Dev.db'
INGESTER_LOG_PATH = 'logs/'

#Refreshing configuration
UPDATE_WINDOW_DAYS = 30
UPDATE_FREQUENCY_HOURS = 3
STARTING_YEAR = 2025
STARTING_DATE = date(STARTING_YEAR, 1, 1)
#Connection Configuration
CONN_DICT = {'EU1':EU1_Conn, 'EU2': EU2_Conn}

#KPI Configuration
SUNRISE_TIME = 6
SUNSET_TIME = 20
SPEED_THRESHOLD = 0.5

#Excel Output Configuration
SUFFIX = '_E_KPI'
