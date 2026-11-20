import os
import sys
import pandas as pd
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from bootstrap_paths import activate

activate()

from locallib.picarrodb import *
from locallib.query import *

from lib.tables.IngesterTables import *
from lib.config import *
from lib.kpi_processor.KPIConfig import KPI_DEFINITIONS

kpi_df = pd.DataFrame(
    [
        {"Name": key, "Unit": value[0], "Description": value[1], "Formula": value[2],'Type': value[3], "LastUpdated": datetime.now()}
        for key, value in KPI_DEFINITIONS.items()
    ]
)
dbo['KPI_Definition'].reinit_table()
dbo['KPI_Definition'].update_table(arguments={'DataFrame': kpi_df,'PrimaryKey': 'Name'})
