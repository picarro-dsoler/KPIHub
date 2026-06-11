from locallib.picarrodb import *
from locallib.query import *

from ..tables.IngesterTables import *
from ..config import *
from ..KPIHubConnection import *
import pandas as pd
from datetime import datetime
def add_customer(customer_name,Conn):
    pull_query = Query(query = f"SELECT C.Id, C.Name FROM Customer C WHERE LOWER(C.Name) = LOWER('{customer_name}')")
    result = pull_query.execute(Conn)
    if result.empty:
        raise ValueError(f"Customer {customer_name} not found")
    else:
        if Conn.database == 'EU-SurveyorProduction':
            DBLocation = 'EU1'
        elif Conn.database == 'EU-SurveyorProduction2':
            DBLocation = 'EU2'
        else:
            DBLocation = 'Unknown'
        short_name = result.iloc[0]['Name'].replace(" ", "")
        # Insert if not exists, otherwise update the row
        # This version uses the correct PK constraint. Double-check that KPI_Customer.CustomerId is PRIMARY KEY or UNIQUE.
        upsert_query = """
            INSERT INTO KPI_Customer (CustomerId, Name, ShortName, DBLocation, LastUpdated)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(CustomerId) DO UPDATE SET
                Name=excluded.Name,
                ShortName=excluded.ShortName,
                DBLocation=excluded.DBLocation,
                LastUpdated=excluded.LastUpdated
        """

        params = (
            result.iloc[0]['Id'],
            result.iloc[0]['Name'],
            short_name,
            DBLocation,
            datetime.now(),
        )
   
 
        KPIHub_Conn.engine.execute(upsert_query, params).fetchall()