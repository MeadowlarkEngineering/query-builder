"""
Count query builder
"""

from typing import Dict, List
from psycopg2 import sql
from query_builder.column_definition import ColumnDefinition
from query_builder.select import Select
from query_builder.postgres_config import PostgresConfig
from query_builder.utilities import get_column_definitions


class Count(Select):
    """Count"""

    def __init__(self, table_name, count_column_name="count"):
        super().__init__(table_name)
        self._count_column_name = count_column_name
        self._columns = [
            sql.SQL("COUNT(*) as {}").format(
                sql.Identifier(f"{table_name}.{count_column_name}")
            )
        ]
        self._group_by_columns = []

    def get_column_definitions(
        self, pg_config: PostgresConfig
    ) -> Dict[str, List[ColumnDefinition]]:
        """
        Returns a dictionary of table_names mapped to column definitions for this command
        """
        # Initialize the column definitions with the count column
        col_definitions = {
            self._table_name: [
                ColumnDefinition(
                    table_name=self._table_name,
                    name=self._count_column_name,
                    data_type="integer",
                    is_nullable=False,
                    default=None,
                )
            ]
        }

        # Add any group by columns
        for table, column in self._group_by_columns:
            defs = get_column_definitions(table, pg_config)
            col_def = next((d for d in defs if d.name == column), None)
            if table in col_definitions:
                col_definitions[table].append(col_def)
            else:
                col_definitions[table] = [col_def]

        return col_definitions

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

        for col in columns:
            # Append a tuple (table, column-name) to the group_by_columns list
            self._group_by_columns.append(
                (self._table_name if table is None else table, col)
            )

            # Append the column to the select columns
            self._columns.append(
                sql.SQL("{}.{} as {}").format(
                    sql.Identifier(self._table_name if table is None else table),
                    sql.Identifier(col),
                    sql.Identifier(f"{self._table_name}.{col}"),
                )
            )
        return self

    @property
    def group_by_sql(self):
        """
        Returns the group by SQL
        """
        if len(self._group_by_columns) > 0:
            # Format the group by clause from the group_by_columns tuples (table, column)
            return sql.SQL("GROUP BY {}").format(
                sql.SQL(",").join(
                    sql.SQL("{}.{}").format(
                        sql.Identifier(c[0]),
                        sql.Identifier(c[1]),
                    )
                    for c in self._group_by_columns
                )
            )

        return sql.SQL("")
