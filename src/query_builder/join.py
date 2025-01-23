"""
Defines a class for generating Join statements
"""

from psycopg2 import sql


class Join:
    """
    Performs join on table
    """

    INNER = "INNER"
    LEFT_OUTER = "LEFT OUTER"

    def __init__(self, *args, **kwargs):
        """Initialization for join"""

        self.tables = []

        if (
            "left_table" in kwargs
            and "right_table" in kwargs
            and "left_col" in kwargs
            and "right_col" in kwargs
        ):
            self.__init_with_table(**kwargs)

        elif "right_table" in kwargs and "on" in kwargs:
            self.__init_with_table_on(**kwargs)

        elif len(args) == 1 and isinstance(args[0], sql.Composable):
            # Trust that argument is a proper sql join statement
            # This constructor will not add anything to self.tables so is not recommended for regular use
            self.sql = args[0]

        elif len(args) == 1 and isinstance(args[0], Join):
            # Trust that argument is a proper Join object
            # This constructor will not add anything to self.tables so is not recommended for regular use
            self.sql = args[0].sql
            self.tables = args[0].tables

        else:
            raise ValueError(f"Invalid initialization of Join with {args} and {kwargs}")

    def __init_with_table_on(
        self, right_table: str, on: str, type=INNER, left_table=None, left_col=None
    ):
        """
        Keyword initialization. It is important that left_col be a column on the parent table in the select clause
        and right_col be a column in the right_table declared in this initializer.  The table names are
        appended to the front of the columns, so mixing these up will result in SQL errors.

        @param {str} right_table The table being joined
        @param {str} on The ON clause
        @param {INNER | OUTER} type INNER or OUTER join
        @param {str} left_table The table joining
        @param {str} left_col Present for method signature consistency, but not used
        """
        if left_table and left_table not in self.tables:
            self.tables.append(left_table)

        if left_col is not None:
            raise ValueError("left_col is not compatibile with the on keyword")

        self.tables.append(right_table)

        self.sql = sql.SQL("{type} JOIN {right_table} ON {on} ").format(
            type=sql.SQL(type),
            right_table=sql.Identifier(right_table),
            on=sql.SQL(on),
        )

    def __init_with_table(
        self,
        left_table: str,
        right_table: str,
        left_col: str,
        right_col: str,
        type=INNER,
    ):
        """
        Keyword initialization. It is important that left_col be a column on the parent table in the select clause
        and right_col be a column in the right_table declared in this initializer.  The table names are
        appended to the front of the columns, so mixing these up will result in SQL errors.

        @param {str} left_table The table joining
        @param {str} right_table The table being joined
        @param {str} left_col The column on the left hand side of the ON equality
        @param {str} right_col The column on the right hand side of the ON equality
        @param {INNER | OUTER} type INNER or OUTER join
        """
        self.tables.append(right_table)

        self.sql = sql.SQL(
            "{type} JOIN {right_table} ON {left_table}.{left_col} = {right_table}.{right_col} "
        ).format(
            type=sql.SQL(type),
            left_table=sql.Identifier(left_table),
            right_table=sql.Identifier(right_table),
            left_col=sql.Identifier(left_col),
            right_col=sql.Identifier(right_col),
        )

    def join(self, *args, **kwargs):
        """
        Returns a new Join object that is a compound of this join and new parameters

        example: Assuming you are joining a comments table with a posts and author table

        join = Join(
                right_table='posts',
                left_col='post_id',
                right_col='id'
            ).join(
                right_table='authors',
                left_col='author_id',
                right_col='id'
            )
        """
        new_join = Join(*args, **kwargs)
        self.sql = sql.Composed([self.sql, new_join.sql])
        self.tables.extend(new_join.tables)

        return self
