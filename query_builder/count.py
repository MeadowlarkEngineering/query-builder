"""
Count query builder
"""
from query_builder.select import Select
from psycopg2 import sql

class Count(Select):
    """Count"""


    def __init__(self, table_name):
        super().__init__(table_name)
        self._columns = [sql.SQL("COUNT(*)")]
        self._group_by_columns = None


    def get_columns(self, table_name, pg_config) -> sql.Composed:
        """
        Override the get_columns method to return only those
        columns specified in the group_by 
        """
        return sql.Composed(self._columns)
    

    def group_by(self, *columns, table=None):
        """
        Group by columns in the table
        """
        self._group_by_columns = []
        for col in columns:

            self._group_by_columns.append(
                 sql.SQL("{}.{}").format(
                        sql.Identifier(self._table_name if table is None else table),
                        sql.Identifier(col),
                      )
            )

            self._columns.append(
                 sql.SQL("{}.{} as {}").format(
                        sql.Identifier(self._table_name if table is None else table),
                        sql.Identifier(col),
                        sql.Identifier(f"{self._table_name}.{col}")
                      )
            )

        return self
    

    @property
    def group_by_sql(self):
        """
        Returns the group by SQL
        """
        if self._group_by_columns is not None:
            return sql.SQL("GROUP BY {}").format(
                sql.SQL(",").join(self._group_by_columns)
            )

        return sql.SQL("")
        