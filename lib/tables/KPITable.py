from locallib.picarrodb import *
import sqlite3

class KPITable(DBTable):
    def __init__(self, name, columns = None):
        super().__init__(name, columns)
    
    def create_table(self, arguments = None):
        if arguments is None:
            raise ValueError("Arguments are required")
        if 'db_path' not in arguments:
            raise ValueError("db_path is required")
        conn = sqlite3.connect(arguments['db_path'])
        cursor = conn.cursor()
        col_defs_list = []
        primary_keys = []
        for column in self.columns:
            col_def = f"{column.name} {column.datatype}"
            if getattr(column, "key", None) == "primary":
                primary_keys.append(column.name)
            col_defs_list.append(col_def)
        col_defs = ", ".join(col_defs_list)
        if primary_keys:
            pk_str = ", PRIMARY KEY (" + ", ".join(primary_keys) + ")"
            col_defs += pk_str
        sql = f"CREATE TABLE IF NOT EXISTS {self.name} ({col_defs})"
   
        cursor.execute(sql)
        conn.commit()
        conn.close()
