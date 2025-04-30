"""
Count query builder
"""

from typing import Dict, List
from psycopg2 import sql
from sqlark.column_definition import ColumnDefinition
from sqlark.select import Select
from sqlark.postgres_config import PostgresConfig


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
        self._group_by_columns: List[ColumnDefinition] = []

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
                    name="*",
                    data_type="integer",
                    is_nullable=False,
                    default=None,
                    function="COUNT",
                    alias=self._count_column_name,
                )
            ]
        }

        # Add any group by columns
        for col_def in self._group_by_columns:
            if col_def.table_name in col_definitions:
                col_definitions[col_def.table_name].append(col_def)
            elif col_def:
                col_definitions[col_def.table_name] = [col_def]

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

            # Append the column to the select columns
            if isinstance(col, ColumnDefinition):
                self._group_by_columns.append(col)
                self._columns.append(col.format_with_alias())
            else:
                col_def = ColumnDefinition(
                    table_name=table or self._table_name,
                    name=col,
                    data_type="text",
                    is_nullable=True,
                    default=None,
                )
                self._group_by_columns.append(col_def)
                self._columns.append(col_def.format_with_alias())

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
                    coldef.format_without_alias() for coldef in self._group_by_columns
                )
            )

        return sql.SQL("")
