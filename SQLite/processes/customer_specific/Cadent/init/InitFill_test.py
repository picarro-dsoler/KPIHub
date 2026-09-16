import os
import sys

directory = os.path.abspath(os.path.dirname(__file__))
_root = os.path.abspath(os.path.join(directory, "..", "..", "..", ".."))

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
add_customer('Cadent',EU2_Conn)

#Add KP Utilization
add_customer_utilization('Cadent', working_days = 7, working_hours = 7, sunrise_hour = 6, sunset_hour = 20, Conn =KPIHub_Conn)

#Add KPI POR
add_por(
    customer_name = 'Cadent',
    year = 2026,
    value = 127780,
    StartingDate = '01-04-2026',
    EndingDate = '31-03-2027',
    Description = ''
)