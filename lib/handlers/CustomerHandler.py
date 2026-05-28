from locallib.picarrodb import *
from locallib.query import *

from ..tables.CustomerTables import *
from ..config import *

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
        upsert_query = """
            INSERT INTO KPI_Customer (Id, Name, ShortName, DBLocation, LastUpdated)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(Id) DO UPDATE SET
                Name=excluded.Name,
                ShortName=excluded.ShortName,
                DBLocation=excluded.DBLocation,
                LastUpdated=excluded.LastUpdated
        """
        # NOTE: Make sure that the "Id" column in the "Customer" table is declared as PRIMARY KEY or UNIQUE.
        # For SQLite, this syntax only works if "Id" has such a constraint.
        # If the Customer table is missing this constraint, you must ALTER the table or define it when creating.
   
 
        params = (
            result.iloc[0]['Id'],
            result.iloc[0]['Name'],
            short_name,
            DBLocation,
            datetime.now(),
        )
   
 
        KPIHub_Conn.engine.execute(upsert_query, params).fetchall()