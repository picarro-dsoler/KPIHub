import os
import sys

directory = os.path.abspath(os.path.dirname(__file__))
_root = os.path.abspath(os.path.join(directory, ".."))

# Add KPIHub root to sys.path so `lib.*` imports resolve regardless of cwd.
sys.path.insert(0, _root)
os.chdir(_root)

from locallib.picarrodb import *
from locallib.query import *

from lib.tables.IngesterTables import *
from lib.handlers.CustomerHandler import *
from lib.config import *
from lib.KPIHubConnection import *

#Add customer
add_customer('ITALGAS',EU2_Conn)
add_customer('Westnetz',EU1_Conn)
add_customer('Toscana Energia',EU2_Conn)
#Add KP Utilization
add_customer_utilization('ITALGAS', working_days = 6, working_hours = 5, sunrise_hour = 7, sunset_hour = 19, Conn =KPIHub_Conn)
add_customer_utilization('Westnetz', working_days = 6, working_hours = 5, sunrise_hour = 8, sunset_hour = 19, Conn = KPIHub_Conn)
add_customer_utilization('Toscana Energia', working_days = 6, working_hours = 5, sunrise_hour = 8, sunset_hour = 19, Conn = KPIHub_Conn)
#Add KPI Output Excel Location
add_output_excel_location('ITALGAS', 401896871043, KPIHub_Conn)
add_output_excel_location('Westnetz', 398249270000, KPIHub_Conn)
add_output_excel_location('Toscana Energia', 401896871043, KPIHub_Conn)
#Add KPI POR
add_por(
    customer_name = 'ITALGAS',
    year = 2026,
    value = 0,
    StartingDate = '01-01-2026',
    EndingDate = '31-12-2026',
    Description = ''
)
add_por(
    customer_name = 'Westnetz',
    year = 2026,
    value = 0,
    StartingDate = '01-01-2026',
    EndingDate = '31-12-2026',
    Description = ''
)
add_por(
    customer_name = 'Toscana Energia',
    year = 2026,
    value = 0,
    StartingDate = '01-01-2026',
    EndingDate = '31-12-2026',
    Description = ''
)
