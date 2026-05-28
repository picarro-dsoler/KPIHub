from locallib.picarrodb import *
import sqlite3
from .config import *
class SQLiteConnection(PConnection):
    def __init__(self, host):
        self.host = host
        self.dbtype = 'sqlite'
        self.engine = sqlite3.connect(host)
    
KPIHub_Conn = SQLiteConnection(DB_PATH)
        
