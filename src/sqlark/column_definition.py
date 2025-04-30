"""
Module for a column definition
"""

from dataclasses import dataclass
from psycopg2 import sql


@dataclass
class ColumnDefinition:
    """
    Represents a column definition
    """

    table_name: str
    name: str
    data_type: str
    is_nullable: bool = True
    default: str | None = None
    is_list: bool = False
    alias: str | None = None
    function: str | None = None

    def __post_init__(self):
        if self.alias is None:
            self.alias = f"{self.table_name}.{self.name}"

    def format_with_alias(self) -> sql.Composed:
        if self.function:
            return sql.SQL("{} {}").format(
                sql.SQL(self.function),
                sql.Identifier(self.alias),
            )

        return sql.SQL("{}.{} as {}").format(
            sql.Identifier(self.table_name),
            sql.Identifier(self.name),
            sql.Identifier(self.alias),
        )

    def format_without_alias(self) -> sql.Composed:
        if self.function:
            return sql.SQL("{}").format(
                sql.SQL(self.function),
            )

        return sql.SQL("{}.{}").format(
            sql.Identifier(self.table_name),
            sql.Identifier(self.name),
        )
