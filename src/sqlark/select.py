"""
Select query builder
"""

from typing import List, Dict
from psycopg2 import sql
from sqlark.join import Join
from sqlark.where import Where
from sqlark.command import SQLCommand
from sqlark.postgres_config import PostgresConfig
from sqlark.utilities import get_columns_composed, get_column_definitions
from sqlark.column_definition import ColumnDefinition


# pylint: disable=too-many-instance-attributes,too-many-public-methods
class Select(SQLCommand):
    """Select"""

    __slots__ = [
        "_table_name",
        "_join",
        "_distinct",
        "_order_by",
        "_limit",
        "_offset",
        "_group_by",
    ]

    def __init__(self, table_name):
        """
        Perpare a select query using table_name as the primary table
        """
        super().__init__()
        self._table_name = table_name
        self._distinct = None
        self._join = None
        self._where = None
        self._order_by = None
        self._limit = None
        self._offset = None
        self._group_by = None

    @property
    def table_name(self):
        """Table name"""
        return self._table_name

    def get_column_definitions(self, pg_config) -> Dict[str, List[ColumnDefinition]]:
        """
        Returns a dictionary with tablenames (keys) mapped to list of column definition objects.
        """
        col_defs = super().get_column_definitions(pg_config)

        # Add the join table column definitions
        join = self.get_join()
        if join is not None:
            for t in join.tables:
                col_defs[t] = get_column_definitions(t, pg_config)

        return col_defs

    def get_columns(self, table_name, pg_config):
        """The sql formatted columns to use building the query"""
        columns = get_columns_composed(table_name, pg_config)

        # Construct the join sql
        join = self.get_join()
        if join is not None:
            for t in join.tables:
                columns = columns + get_columns_composed(t, pg_config)

        return columns

    def join(self, join: Join | None = None, **kwargs):
        """
        Join another table
        params:
            a join object or keyword arguments for construction a join object
            If left_table is not provided, it defaults to the primary table
            If left_col is not provided, it defaults to "id"

        @return {Select} self
        """

        if "left_table" not in kwargs:
            kwargs["left_table"] = self._table_name

        if "left_col" not in kwargs:
            kwargs["left_col"] = "id"

        if self._join is None:
            self._join = Join(join, **kwargs)
        else:
            if join is not None:
                self._join.join(join)
            else:
                self._join.join(**kwargs)

        return self

    def get_join(self):
        """
        Returns the join
        This does not return the SQL, because the client aliases the table names
        """
        return self._join

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

    def where_in(self, column, values, table=None):
        """
        Appends a where clause using IN
        """
        if self._where is None:
            self._where = Where()
        self._where.where_in(column, values, table)
        return self

    def order_by(self, column, table=None, direction="ASC"):
        """
        Order by a column or columns
        """
        if isinstance(column, str):
            self._order_by = sql.SQL("ORDER BY {}.{} {}").format(
                sql.Identifier(self._table_name if table is None else table),
                sql.Identifier(column),
                sql.SQL(direction),
            )
        if isinstance(column, list):
            self._order_by = sql.SQL("ORDER BY {}").format(
                sql.SQL(", ").join(
                    [
                        sql.SQL("{table}.{column} {direction}").format(
                            table=sql.Identifier(
                                self._table_name if table is None else table
                            ),
                            column=sql.Identifier(c),
                            direction=sql.SQL(direction),
                        )
                        for c in column
                    ]
                )
            )

        return self

    def distinct(self, columns):
        """
        Distinct
        """
        if isinstance(columns, str):
            self._distinct = sql.SQL("DISTINCT {}").format(sql.Identifier(columns))
        else:
            self._distinct = sql.SQL("DISTINCT {}").format(
                sql.SQL(", ").join([sql.Identifier(c) for c in columns])
            )

        return self

    @property
    def order_by_sql(self):
        """
        Returns the order by SQL
        """
        if self._order_by is None:
            return sql.SQL("")
        return self._order_by

    def limit(self, limit):
        """
        Limit the number of rows returned
        """
        self._limit = sql.SQL("LIMIT {}").format(sql.Literal(limit))
        return self

    @property
    def limit_sql(self):
        """
        Returns the limit SQL
        """
        if self._limit is None:
            return sql.SQL("")
        return self._limit

    def offset(self, offset):
        """
        Offset the number of rows returned
        """
        self._offset = sql.SQL("OFFSET {}").format(sql.Literal(offset))
        return self

    @property
    def offset_sql(self):
        """
        Returns the offset SQL
        """
        if self._offset is None:
            return sql.SQL("")
        return self._offset

    def group_by(self, column, table=None):
        """
        Group by a column
        """
        self._group_by = sql.SQL("GROUP BY {}.{}").format(
            sql.Identifier(self._table_name if table is None else table),
            sql.Identifier(column),
        )
        return self

    @property
    def group_by_sql(self):
        """
        Returns the group by SQL
        """
        if self._group_by is None:
            return sql.SQL("")
        return self._group_by

    def to_sql(self, pg_config: PostgresConfig) -> sql.SQL:
        """
        Overrides the SQLCommand to_sql method
        """
        table_name = self.table_name
        columns = self.get_columns(table_name, pg_config)

        # Construct the join sql
        join = self.get_join()
        if join is not None:
            join_sql = join.sql
        else:
            join_sql = sql.SQL("")

        # Construct the where sql
        if self._where is not None:
            where_sql = sql.SQL(" WHERE {where}").format(where=self._where.sql)
        else:
            where_sql = sql.SQL("")

        # Construct order by and limit
        order_by = self.order_by_sql
        group_by = self.group_by_sql
        limit = self.limit_sql
        offset = self.offset_sql

        # Combine the sql
        command = sql.SQL(
            "SELECT {columns} FROM {table} {join} {where} {order_by} {group_by} {offset} {limit}"
        ).format(
            columns=columns.join(",") if self._distinct is None else self._distinct,
            table=sql.Identifier(table_name),
            join=join_sql,
            where=where_sql,
            order_by=order_by,
            group_by=group_by,
            offset=offset,
            limit=limit,
        )

        return command

    def get_params(self):
        """
        Returns the parameters for the where clause
        """
        if self._where is None:
            return []
        return self._where.params

    def execute(self, pg_config: PostgresConfig, transactional=False):
        """
        Executes the command
        params:
            pg_config: PostgresConfig The configuration for the postgres connection
            transactional: bool Whether to execute the command in a transaction
        """
        command = self.to_sql(pg_config)
        params = self.get_params()

        with pg_config.connect_with_cursor(transactional=transactional) as cursor:
            self.logger.debug(command.as_string(cursor))
            if params:
                self.logger.debug(params)
                cursor.execute(command, params)
            else:
                cursor.execute(command)

            return self._response_formatter(cursor.fetchall(), pg_config, self)
