from locallib.picarrodb import *
import os
import re
import sqlite3
import sys
from lib.views.ViewConfig import KPI_CUSTOMER_VIEWS

# lib/ is not on sys.path when imported as lib.tables.*; sibling modules use flat imports.
_lib_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _lib_dir not in sys.path:
    sys.path.insert(0, _lib_dir)

from lib.config import KPIHUB_CONNECTION
from lib.tables.TableConfig import TABLE_CONFIG_LIST
from lib.tables.KPITable import KPITable

dbo = {}
for table_config in TABLE_CONFIG_LIST:
    table_name = table_config['Name']
    table_columns = table_config['Columns']
    table_primary_key = table_config['PrimaryKey']
    dbo[table_name] = KPITable(table_name, connection=KPIHUB_CONNECTION)
    for col in table_columns.keys():
        if col == table_primary_key:
            dbo[table_name].add_column(DBColumn(col, datatype=table_columns[col], key='primary'))
        else:
            dbo[table_name].add_column(DBColumn(col, datatype=table_columns[col]))

column_name_map = {}
for _table in dbo.values():
    for c in _table.columns:
        column_name_map[c.name.lower()] = c.name
for kpi_view in KPI_CUSTOMER_VIEWS:
    for col in kpi_view["Columns"].keys():
        column_name_map[col.lower()] = col

column_name_map['customername'] = 'CustomerName'
column_name_map['customerid'] = 'CustomerId'
