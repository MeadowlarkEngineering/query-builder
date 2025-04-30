"""
Insert query builder
"""

from psycopg2 import sql
from psycopg2.extras import execute_values
from sqlark.logger import get_logger
from sqlark.command import SQLCommand
from sqlark.postgres_config import PostgresConfig

logger = get_logger(__name__)


class Insert(SQLCommand):
    """Insert query builder"""

    def __init__(self, table_name):
        """
        Perpare an insert query using table_name as the primary table
        """
        super().__init__()
        self._table_name = table_name
        self._where = None
        self._on_conflict_constraints = None
        self._on_conflict_action = None
        self._values = None

    @property
    def table_name(self):
        """Table name"""
        return self._table_name

    def on_conflict(self, constraint: str | list[str], action: str):
        """
        Add an on_conflict clause
        params:
            constraint: list[str] The constraint columns to check
            action: str The action to take.  Either "nothing" or "update"
        """
        self._on_conflict_constraints = constraint
        self._on_conflict_action = action
        return self

    def on_conflict_sql(self, update_columns: list[sql.Identifier]):
        """
        Returns the on_conflict by SQL
        params:
            update_columns: list[str] The columns to update on conflict if the action is "update"
        """
        if self._on_conflict_constraints is None:
            return sql.SQL("")

        if isinstance(self._on_conflict_constraints, list):
            constraint = sql.SQL(",").join(
                [sql.Identifier(c) for c in self._on_conflict_constraints]
            )

        else:
            constraint = sql.Identifier(self._on_conflict_constraints)

        if self._on_conflict_action.lower() == "nothing":
            action_sql = sql.SQL("DO NOTHING")
        elif self._on_conflict_action.lower() == "update":
            action_sql = sql.SQL("DO UPDATE SET {}").format(
                sql.SQL(",").join(
                    [
                        sql.Composed(
                            [
                                col,
                                sql.SQL(" = COALESCE(EXCLUDED."),
                                col,
                                sql.SQL(", "),
                                sql.Identifier(self._table_name),
                                sql.SQL("."),
                                col,
                                sql.SQL(")"),
                            ]
                        )
                        for col in update_columns
                    ]
                )
            )
        else:
            raise ValueError(f"Invalid action {self._on_conflict_action}")

        clause = sql.SQL("ON CONFLICT ({}) {}").format(constraint, action_sql)
        return clause

    def values(self, values: dict | list[dict]):
        """
        Add values to insert.  The values should be a dictionary or a list of dictionaries if inserting multiple rows.
        The keys of each dict should be the column names and the values should be the values to insert.
        params:
            values: dict | list[dict] The values to insert
        """
        if not isinstance(values, list):
            values = [values]

        self._values = values
        return self

    @property
    def columns(self):
        """
        The columns to update, as extracted from the values
        """
        columns = []
        for value in self._values:
            columns.extend([k for k in value.keys() if k not in columns])

        return sorted(columns)

    def to_sql(self, pg_config: PostgresConfig) -> sql.SQL:
        """
        Overrides the SQLCommand to_sql method
        """
        table_name = self.table_name

        columns = [sql.Identifier(c) for c in self.columns]

        # Combine the sql
        command = sql.SQL(
            "INSERT INTO {table} ({columns}) VALUES %s {on_conflict} RETURNING *"
        ).format(
            table=sql.Identifier(table_name),
            columns=sql.Composed(columns).join(","),
            on_conflict=self.on_conflict_sql(columns),
        )
        return command

    def execute(self, pg_config: PostgresConfig, transactional=False):
        """
        Executes the command
        params:
            pg_config: PostgresConfig The configuration for the postgres connection
            transactional: bool Whether to execute the command in a transaction
        """
        command = self.to_sql(pg_config)

        # Construct a template for values to insert
        named_value_template = (
            "(" + ", ".join([f"%({col})s" for col in self.columns]) + ")"
        )

        with pg_config.connect_with_cursor(transactional=transactional) as cursor:
            self.logger.debug(command.as_string(cursor))
            execute_values(
                cursor,
                command,
                self._values,
                template=named_value_template,
                page_size=1000,
            )
            return self._response_formatter(cursor.fetchall(), pg_config, self)
