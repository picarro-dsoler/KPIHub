import os
import sys
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from bootstrap_paths import activate

activate()

directory = os.path.abspath(os.path.dirname(__file__))

import sqlite3

from locallib.picarrodb import *
from locallib.query import *

from lib.tables.IngesterTables import *
from lib.tables.TableConfig import TABLE_CONFIG_LIST
from lib.config import *

_primary_key_by_table = {cfg["Name"]: cfg["PrimaryKey"] for cfg in TABLE_CONFIG_LIST}

# Create tables (composite PKs need pair_key so Postgres ON CONFLICT works).
for table in dbo.keys():
    pk = _primary_key_by_table.get(table)
    if isinstance(pk, list):
        dbo[table].reinit_table(arguments={"pair_key": pk})
    else:
        dbo[table].reinit_table()