"""
Defines a class for aggregating SQL WHERE clauses
"""

from psycopg2 import sql
from sqlark.utilities import PYTHON_DATA_TYPE


class Where:
    """
    Use Where to create and aggregate where clauses.

    example usage:

        w = Where(
                table="posts", column="author", operator="=", value="Clark Kent"
            ).sql_or(
                table="posts", column="created_at", operator=">", value="2023-04-14"
            ).sql_and(
                table="posts", column="text", operator="like", value="%up and away%"
            )
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize with 2 or 4 or kwargs

        2 argument initializer
        @param clause : sql.Composable
        @param list   : values

        4 kwargs initializer
        @param table : str
        @param column : str
        @param operator : str
        @param value : any
        """

        if len(args) == 2:
            # assume (Composable, Params) format
            if isinstance(args[0], sql.Composable) and isinstance(args[1], list):
                self.sql = args[0]
                self.params = args[1]

            else:
                raise AttributeError("Unknown argument types initializing Where")

        elif len(args) == 1 and isinstance(args[0], Where):
            # Trust that argument is a proper Where object
            self.sql = args[0].sql
            self.params = args[0].params

        elif (
            "table" in kwargs
            and "column" in kwargs
            and "operator" in kwargs
            and "value" in kwargs
        ):
            self.__init__from_table_column_operator_value(**kwargs)

        else:
            raise AttributeError("Unknown arguments when initializing Where")

    def __init__from_table_column_operator_value(
        self, table: str, column: str, operator: str, value: PYTHON_DATA_TYPE
    ):
        """
        Each where clause establishes a criteria where a particular column of a specific table is evaluated
        against a value using an operator
        """
        self.sql = sql.SQL("{table}.{column} {operator} {placeholder}").format(
            table=sql.Identifier(table),
            column=sql.Identifier(column),
            operator=sql.SQL(operator),
            placeholder=sql.Placeholder(),
        )
        self.params = [value]

    def sql_and(self, *args, **kwargs):
        """
        Append another where clause onto this where clause using AND returning a Compounded where clause

        w = Where(table='posts', column='created_at', operator='>', value='2023-04-18').sql_and(
                table='posts', column='author', operator='=', value='Clark Kent'
            )

        outputs: " clause1 AND clause 2 "

        If a Where clause is passed as an argument, then automatically apply grouping parenthesis around it:

        w = Where(sql.SQL('"posts"."author" = %s'), ["Clark Kent"]).sql_and(
            Where(
                table="posts", column="created_at", operator=">", value="2023-04-14"
            ).sql_or(
                table="posts", column="text", operator="like", value="%up and away%"
            )
        )

        outputs: " clause1 AND ( clause2 OR clause 3 ) "

        """
        if len(args) == 1 and isinstance(args[0], Where):
            # If a Where clause is passed as an argument, apply grouping parenthesis
            w = Where(sql.SQL("( {} )").format(args[0].sql), args[0].params)
            return self._sql_combine(w, " AND ")

        return self._sql_combine(Where(*args, **kwargs), " AND ")

    def sql_or(self, *args, **kwargs):
        """
        Append anothere where clause onto this where clause using OR returning a Compounded where clause
        Same rules apply as sql_and
        """
        if len(args) == 1 and isinstance(args[0], Where):
            # If a Where clause is passed as an argument, apply grouping parenthesis
            w = Where(sql.SQL("( {} )").format(args[0].sql), args[0].params)
            return self._sql_combine(w, " OR ")

        return self._sql_combine(Where(*args, **kwargs), " OR ")

    def _sql_combine(self, where, logical_operator):
        """
        Combines this Where with another Where using logical_operator
        """
        clause = sql.SQL(logical_operator).join([self.sql, where.sql])
        params = self.params + where.params
        return Where(clause, params)
