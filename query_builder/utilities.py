"""
Useful standalone mixins
"""

from typing import Union
from dataclasses import make_dataclass
from collections import namedtuple
from datetime import datetime
import logging
from psycopg2 import sql
from query_builder.postgres_config import PostgresConfig

TABLE_COLUMN_CACHE = {}
DATACLASS_CACHE = {}

ColumnDefinition = namedtuple(
    "ColumnDefinition", ["name", "data_type", "is_nullable", "default"]
)


def get_logger(name):
    """
    Returns a preconfigured logger
    """
    return logging.getLogger(name)


def get_columns(table_name, pg_config: PostgresConfig, use_cache=True) -> list[str]:
    """
    Retrieves the fields of the table entity_type.

    params:
        table_name: str The name of the table to retrieve the fields from
        use_cache: bool Return the cached value if available
    returns:
        list[str] The fields of the table
    raises:
        ValueError: If the fields could not be retrieved
    """
    columns = get_column_definitions(table_name, pg_config, use_cache=use_cache)
    return [c.name for c in columns]


def get_column_definitions(
    table_name, pg_config: PostgresConfig, use_cache=True
) -> list[ColumnDefinition]:
    """
    Retrieves the column definitions of the table.
    """

    if use_cache and table_name in TABLE_COLUMN_CACHE:
        return TABLE_COLUMN_CACHE[table_name]

    try:
        command = sql.SQL(
            """
            SELECT column_name name, data_type, is_nullable, column_default default
            FROM information_schema.columns 
            WHERE table_name=%s
            """
        )
        params = [table_name]
        with pg_config.connect_with_cursor() as cursor:
            cursor.execute(command, params)
            result = cursor.fetchall()

        columns = [ColumnDefinition(**v) for v in result]
        TABLE_COLUMN_CACHE[table_name] = columns

        if len(columns) == 0:
            raise ValueError(f"Table {table_name} has no columns")

        return columns

    except Exception as e:
        raise ValueError(
            f"Could not retrieve the fields for {table_name} - {str(e)}"
        ) from e


def get_columns_composed(
    table_name, pg_config: PostgresConfig, use_cache=True
) -> sql.Composed:
    """
    Retrieves the table columns as a Composed
    where each column is aliased as "table_name"."column_name"
    params:
        table_name: str The name of the table
    returns:
        sql.Composed The columns of the table as a composed SQL object
    raises:
        ValueError: If the columns could not be retrieved
    """
    format_method = lambda x: sql.SQL("{}.{} as {}").format(
        sql.Identifier(table_name),
        sql.Identifier(x),
        sql.Identifier(f"{table_name}.{x}"),
    )

    return sql.Composed(
        [
            format_method(c)
            for c in get_columns(table_name, pg_config, use_cache=use_cache)
        ]
    )


def data_type_to_field_type(data_type: str, is_nullable: bool = True) -> type:
    """
    Converts a postgres data type to a python data type
    """
    data_type_map = {
        "character varying": str,
        "text": str,
        "integer": int,
        "double precision": float,
        "timestamp without time zone": datetime,
    }
    if is_nullable:
        return Union[data_type_map.get(data_type, str), None]

    return data_type_map.get(data_type, str)


def dataclass_for_table(table_name: str, pg_config: PostgresConfig):
    """
    Generates a new class for the table with each column as an attribute
    """
    if table_name in DATACLASS_CACHE:
        return DATACLASS_CACHE[table_name]

    column_defs = get_column_definitions(table_name, pg_config)

    fields = [
        (c.name, data_type_to_field_type(c.data_type, c.is_nullable))
        for c in column_defs
    ]
    DATACLASS_CACHE[table_name] = make_dataclass(table_name.title(), fields)
    return DATACLASS_CACHE[table_name]


def decompose_row(d: dict):
    """
    Decomposes the keys of a dictionary that have the format "table_name.column_name"
    into a dictionary {table_name: {column_name: value, ...}, table_name2: {column_name: value, ...}, ...}
    """
    result_d = {}
    for k, v in d.items():
        if "." in k:
            table, column = k.split(".")
            if table not in result_d:
                result_d[table] = {}
            result_d[table][column] = v
        else:
            result_d[k] = v

    return result_d
