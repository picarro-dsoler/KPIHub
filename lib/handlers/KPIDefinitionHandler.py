from locallib.picarrodb import *
from locallib.query import *

from ..tables.IngesterTables import *
from ..config import *
from ..KPIHubConnection import *
import pandas as pds
from datetime import datetime

def add_KPI_Definition(name, formula, description, type, value_timestamp):
    KPI_Definition.add_row(arguments={'name': name, 'formula': formula, 'description': description, 'type': type, 'value_timestamp': value_timestamp})