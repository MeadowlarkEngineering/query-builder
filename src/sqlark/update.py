"""
Update query builder
"""

from psycopg2 import sql
from sqlark.logger import get_logger
from sqlark.command import SQLCommand
from sqlark.postgres_config import PostgresConfig
from sqlark.where import Where

logger = get_logger(__name__)


class Update(SQLCommand):
    """Insert query builder"""

    def __init__(self, table_name):
        """
        Perpare an insert query using table_name as the primary table
        """
        super().__init__()
        self._table_name = table_name
        self._where = None
        self._columns = None
        self._values = None

    @property
    def table_name(self):
        """Table name"""
        return self._table_name

    def set(self, values: dict):
        """
        Set the columns and values to update
        params:
            values: list The values to update
        """
        if self._values is None:
            self._values = {}

        for column, value in values.items():
            self._values[column] = sql.Literal(value)

        return self

    def increment(self, column: str, value: int = 1):
        """
        Increment a column by a value
        """
        if self._values is None:
            self._values = {}
        self._values[column] = sql.SQL("{column} + {value}").format(
            column=sql.Identifier(column), value=sql.Literal(value)
        )
        return self

    def where(self, where: Where | None = None, **kwargs):
        """
        Appends a where clause. If a where clause already exists, delegates to where_and
        @return {Select} self
        """
        if "table" not in kwargs:
            kwargs["table"] = self._table_name

        if self._where is None:
            self._where = Where(where, **kwargs)
        else:
            self.where_and(Where(where, **kwargs))

        return self

    def where_and(self, where: Where | None = None, **kwargs):
        """
        Appends a where clause using AND
        """
        if "table" not in kwargs:
            kwargs["table"] = self._table_name

        if self._where is None:
            self._where = Where(where, **kwargs)
        else:
            self._where = self._where.sql_and(Where(where, **kwargs))
        return self

    def where_or(self, where: Where | None = None, **kwargs):
        """
        Appends a where clause using OR
        """
        if "table" not in kwargs:
            kwargs["table"] = self._table_name

        if self._where is None:
            self._where = Where(where, **kwargs)
        else:
            self._where = self._where.sql_or(Where(where, **kwargs))
        return self

    @property
    def columns(self):
        """
        The columns to update, as extracted from the values
        """
        columns = self._values.keys()

        return sorted(columns)

    def to_sql(self, pg_config: PostgresConfig) -> sql.SQL:
        """
        Overrides the SQLCommand to_sql method
        """
        table_name = self.table_name

        # Construct the set sql
        assignments = [
            sql.SQL("{}={}").format(sql.Identifier(c), self._values[c])
            for c in self.columns
        ]
        set_sql = sql.SQL("SET {}").format(sql.SQL(",").join(assignments))

        # Construct the where sql
        if self._where is not None:
            where_sql = sql.SQL(" WHERE {where}").format(where=self._where.sql)
        else:
            where_sql = sql.SQL("")

        # Combine the sql
        command = sql.SQL("UPDATE {table} {set_sql} {where_sql} RETURNING *").format(
            table=sql.Identifier(table_name), set_sql=set_sql, where_sql=where_sql
        )
        return command

    def get_params(self):
        """
        Returns the parameters for the where clause
        """

        if self._where is not None:
            return self._where.params

        return []

    def execute(self, pg_config: PostgresConfig, transactional=False):
        """
        Executes the command
        params:
            pg_config: PostgresConfig The configuration for the postgres connection
            transactional: bool Whether to execute the command in a transaction
        """
        command = self.to_sql(pg_config)

        with pg_config.connect_with_cursor(transactional=transactional) as cursor:
            self.logger.debug(command.as_string(cursor))
            cursor.execute(command, self.get_params())
            return self._response_formatter(cursor.fetchall(), pg_config, self)
