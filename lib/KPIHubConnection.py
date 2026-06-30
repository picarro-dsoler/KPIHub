from locallib.picarrodb import *
import sqlite3
from config import *

import os
import sys

# Get the absolute path of the current file's directory
directory = os.path.abspath(os.path.dirname(__file__))

# Just add the parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(directory, "..")))

class SQLiteConnection(PConnection):
    def __init__(self, host):
        self.host = host
        self.dbtype = 'sqlite'
        self.engine = sqlite3.connect(host)

# Ensure path to DB is relative to this file's directory
db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", DB_PATH))
KPIHub_Conn = SQLiteConnection(db_path)
        
