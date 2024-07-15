"""
Select query builder
"""

from psycopg2 import sql
from query_builder.utilities import get_logger
from query_builder.join import Join
from query_builder.where import Where
from query_builder.command import SQLCommand
from query_builder.postgres_config import PostgresConfig
from query_builder.utilities import get_columns_composed

logger = get_logger(__name__)


class Select(SQLCommand):
    """Select"""

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


    def join(self, join: Join | None = None, **kwargs):
        """
        Join another table
        params:
            a join object or keyword arguments for construction a join object
        @return {Select} self
        """
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

    def order_by(self, column, table=None, direction="ASC"):
        """
        Order by a column
        """
        self._order_by = sql.SQL("ORDER BY {}.{} {}").format(
            sql.Identifier(self._table_name if table is None else table),
            sql.Identifier(column),
            sql.SQL(direction),
        )
        return self

    def distinct(self, columns):
        """
        Distinct
        """
        print(isinstance(columns, str))
        if isinstance(columns, str):
            self._distinct = sql.SQL("DISTINCT {}").format(sql.Identifier(columns))
        else:
            self._distinct = sql.SQL("DISTINCT {}").format(sql.SQL(", ").join([sql.Identifier(c) for c in columns]))

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
        columns = get_columns_composed(table_name, pg_config)

        # Construct the join sql
        join = self.get_join()
        if join is not None:
            join_sql = join.sql
            # Add joined table columns to select
            for t in join.tables:
                columns = columns + get_columns_composed(t, pg_config)
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
            return [dict(r) for r in cursor.fetchall()]
