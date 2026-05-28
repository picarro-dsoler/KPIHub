from locallib.picarrodb import *
from .KPITable import *

# Customer Table
KPI_Customer = KPITable('KPI_Customer')
KPI_Customer.add_column(DBColumn('Id', datatype='uniqueidentifier', key='primary'))
KPI_Customer.add_column(DBColumn('Name', datatype='nvarchar'))
KPI_Customer.add_column(DBColumn('ShortName', datatype='nvarchar'))
KPI_Customer.add_column(DBColumn('DBLocation', datatype='nvarchar'))
KPI_Customer.add_column(DBColumn('LastUpdated', datatype='datetime'))