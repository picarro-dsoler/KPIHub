"""Minimal DBTable / DBColumn (same responsibilities as packages/locallib/picarrodb.PicarroDBClass)."""


class DBTable:
    def __init__(self, name, columns=None):
        self.name = name
        self.alias = name
        self.columns = columns if columns is not None else []
        self.acronym = "".join([char for char in name if char.isupper()])
        for column in self.columns:
            column.parent_table = self
            setattr(self, column.name, column)

    def get_table_name(self):
        return self.name

    def get_acronym(self):
        return self.acronym

    def get_table_alias(self):
        return self.alias

    def create_table(self, arguments=None):
        raise NotImplementedError

    def get_columns(self, format="query"):
        if format == "query":
            query = [
                (
                    f"{self.acronym}.{column.get_column_name()}.STAsText() as {column.get_column_alias()}"
                    if column.datatype == "geometry"
                    else f"{self.acronym}.{column.get_column_name()} as {column.get_column_alias()}"
                )
                for column in self.columns
            ]
            return " , ".join(query)
        if format == "list":
            return [f"{column.get_column_name()}" for column in self.columns]
        raise ValueError(f"Invalid format: {format}")

    def add_column(self, column):
        self.columns.append(column)
        setattr(self, column.name, column)

    def __repr__(self):
        return f"{self.name}"

    def set_column_alias(self, column_name, alias):
        for col in self.columns:
            if col.name == column_name:
                col.set_column_alias(alias)
                return
        raise ValueError(f"Column {column_name} not found in table {self.name}")

    def delete_column(self, column_name):
        for col in self.columns:
            if col.name == column_name:
                self.columns.remove(col)
                delattr(self, col.name)
                return
        raise ValueError(f"Column {column_name} not found in table {self.name}")

    def copy(self):
        return DBTable(self.name, self.columns.copy())


class DBColumn:
    def __init__(self, name, datatype=None, key=None):
        self.name = name
        self.datatype = datatype
        self.alias = name
        self.key = key
        if key is not None and key not in ("primary", "foreign"):
            raise ValueError(f"Invalid key: {key}")

    def get_column_name(self):
        return self.name

    def set_column_alias(self, alias):
        self.alias = alias

    def get_column_alias(self):
        return self.alias

    def __repr__(self):
        return f"{self.name}"
