"""
Delete query builder
"""

from psycopg2 import sql
from sqlark.logger import get_logger
from sqlark.command import SQLCommand
from sqlark.postgres_config import PostgresConfig
from sqlark.where import Where

logger = get_logger(__name__)


class Delete(SQLCommand):
    """Delete query builder"""

    def __init__(self, table_name):
        """
        Perpare a delete query using table_name as the primary table
        """
        super().__init__()
        self._table_name = table_name
        self._where = None

    @property
    def table_name(self):
        """Table name"""
        return self._table_name

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

    def to_sql(self, pg_config: PostgresConfig) -> sql.SQL:
        """
        Overrides the SQLCommand to_sql method
        """
        table_name = self.table_name

        # Construct the where sql
        if self._where is not None:
            where_sql = sql.SQL("WHERE {where}").format(where=self._where.sql)
        else:
            where_sql = sql.SQL("")

        # Combine the sql
        command = sql.SQL("DELETE FROM {table} {where_sql} RETURNING *").format(
            table=sql.Identifier(table_name), where_sql=where_sql
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
