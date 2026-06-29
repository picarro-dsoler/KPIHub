from locallib.picarrodb import *
import sqlite3
import uuid
from datetime import date, datetime, time
import pandas as pd

class KPITable(DBTable):
    def __init__(self, name, columns = None):
        super().__init__(name, columns)
    
    def delete_table(self, arguments = None):
        if arguments is None:
            raise ValueError("Arguments are required")
        if 'db_path' not in arguments:
            raise ValueError("db_path is required")
        conn = sqlite3.connect(arguments['db_path'])
        cursor = conn.cursor()
        cursor.execute(f"DROP TABLE IF EXISTS {self.name}")
        conn.commit()
        conn.close()


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
        if 'pair_key' in arguments and arguments['pair_key'] is not None:
            col_defs += f" , PRIMARY KEY ({', '.join(arguments['pair_key'])})"
        sql = f"CREATE TABLE IF NOT EXISTS {self.name} ({col_defs})"

        print(sql)
        cursor.execute(sql)
        if 'extra_sql' in arguments and arguments['extra_sql'] is not None:
            cursor.execute(arguments['extra_sql'])
        conn.commit()
        conn.close()

    def reinit_table(self, arguments = None, extra_sql = None):
        if arguments is None:
            raise ValueError("Arguments are required")
        if 'db_path' not in arguments:
            raise ValueError("db_path is required")
        arguments_db_path = arguments['db_path']
        self.delete_table(arguments = {'db_path': arguments_db_path})
        self.create_table(arguments = arguments)

    def query_table(self, arguments = None):
        if arguments is None:
            raise ValueError("Arguments are required")
        if 'db_path' not in arguments:
            raise ValueError("db_path is required")
        df = pd.read_sql_query(f"SELECT * FROM {self.name}", sqlite3.connect(arguments['db_path']))
   
        return df

    def update_table(self, arguments = None):
        #Load the content of the df into a temp table
        #Bulk update
        df = arguments['DataFrame']
        primary_key = arguments['PrimaryKey']
        if isinstance(primary_key, list):
            pk_cols = set(primary_key)
            primary_key = ','.join(primary_key)
        elif isinstance(primary_key, str):
            pk_cols = {primary_key}
            primary_key = primary_key
        else:
            raise ValueError("PrimaryKey must be a list of strings or a single string")

        conn = sqlite3.connect(arguments['db_path'])
        cursor = conn.cursor()

        cols = df.columns.tolist()
        columns = ", ".join(cols)
        placeholders = ", ".join(["?"] * len(cols))
        updates = ", ".join([f"{col}=excluded.{col}" for col in cols if col not in pk_cols])

        insert_sql = f"""
            INSERT INTO {self.name} ({columns})
            VALUES ({placeholders})
            ON CONFLICT({primary_key}) DO UPDATE SET
            {updates};
        """

        # To avoid the InterfaceError, convert unsupported types to sqlite-bindable values.
        def clean_value(val):
            if pd.isna(val):
                return None
            if isinstance(val, pd.Timestamp):
                return val.to_pydatetime()
            if isinstance(val, datetime):
                return val
            if isinstance(val, time):
                return val.isoformat()
            if isinstance(val, date):
                return val.isoformat()
            if isinstance(val, uuid.UUID):
                return str(val)
            if hasattr(val, "item"):  # handles numpy scalars
                return val.item()
            return val

        data = [tuple(clean_value(row[col]) for col in cols) for _, row in df.iterrows()]
        cursor.executemany(insert_sql, data)  # use executemany for efficiency

        conn.commit()
        conn.close()
 