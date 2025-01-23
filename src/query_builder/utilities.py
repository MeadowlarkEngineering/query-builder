"""
Useful standalone mixins
"""

from typing import Union, Dict
from dataclasses import make_dataclass, dataclass, field
from datetime import datetime
from psycopg2 import sql
from query_builder.postgres_config import PostgresConfig
from query_builder.column_definition import ColumnDefinition

TABLE_COLUMN_CACHE = {}

POSTGRES_DATA_TYPES = {
    "character varying": str,
    "text": str,
    "integer": int,
    "double precision": float,
    "timestamp without time zone": datetime,
    "ARRAY": list,
}


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
            SELECT table_name, column_name name, data_type, is_nullable, column_default default
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


def is_postgres_datatype(data_type: str) -> bool:
    """
    Returns True if the data_type is a postgres data type
    """
    return data_type in POSTGRES_DATA_TYPES


def data_type_to_field_type(data_type: str, is_nullable: bool = True) -> type:
    """
    Converts a postgres data type to a python data type
    If data_type is not recognized return None
    """

    if data_type in POSTGRES_DATA_TYPES:
        dtype = POSTGRES_DATA_TYPES[data_type]
    else:
        return None

    if is_nullable:
        return Union[dtype, None]

    return dtype


def make_eq_method(fields_to_compare):
    """
    Generates an equality method that only compares the fields in fields_to_compare
    """

    def eq(self, other):
        if not isinstance(other, type(self)):
            return False
        return all(
            getattr(self, f[0]) == getattr(other, f[0]) for f in fields_to_compare
        )

    return eq


def build_dataclasses(
    class_definitions: Dict[str, list[ColumnDefinition]]
) -> Dict[str, dataclass]:
    """
    Generate dataclasses given a dictionary of {class_name: column_definitions}
    Returns a dictionary of {class_name: dataclass}

    This function will construct dataclasses with primitive attributes first.
    Classes with complex datatypes (i.e. another class represented in class_definitions) will only be
    created if their dependencies have been resolved. If a class has a complex data field that cannot be resolved,
    it is deferred until all other classes have been constructed.
    If a class deferred class still cannot be resolved after all other classes are created, then a ValueError is raised.
    """
    complex_classes = []
    built_classes = {}
    # Construct the classes with no complex data fields first
    for class_name, columns in class_definitions.items():

        if class_name in built_classes:
            continue

        # If any of the columns are not postgres data types, defer the class
        if not all(is_postgres_datatype(c.data_type) for c in columns):
            complex_classes.append(class_name)
            continue

        fields = [
            (c.name, data_type_to_field_type(c.data_type, c.is_nullable))
            for c in columns
        ]
        built_classes[class_name] = make_dataclass(class_name.title(), fields)

    # Construct the classes with complex data fields
    # If a class has a complex data field that cannot be resolved, it is deferred
    # until all other classes have been constructed
    deferred_classes = []
    while len(complex_classes) > 0:

        class_name = complex_classes.pop()

        # If any of the columns are not postgres data types and are not in the Dataclass Cache, defer the creation
        if any(
            (
                (data_type_to_field_type(c.data_type, c.is_nullable) is None)
                and (c.data_type not in built_classes)
            )
            for c in class_definitions[class_name]
        ):
            if class_name in deferred_classes:
                # Break the cycle
                raise ValueError(
                    f"Could not resolve complex data type for {class_name}"
                )
            # Note that the class is deferred and try again later
            deferred_classes.append(class_name)
            # Put the class back in the queue
            complex_classes.insert(0, class_name)
            # restart the while loop
            continue

        # pylint: disable=invalid-field-call
        base_fields = []  # primitive postgres fields, used for equality comparison
        fields = []  # All fields including postgres and dataclass fields
        for c in class_definitions[class_name]:
            dtype = data_type_to_field_type(c.data_type, c.is_nullable)

            if c.is_list:
                f = (c.name, list[dtype], field(default_factory=list))
            else:
                f = (c.name, dtype, field(default=c.default))

            if is_postgres_datatype(c.data_type):
                base_fields.append(f)

            fields.append(f)

        # Construct a base class with all the fields but no equal method
        base_dc = make_dataclass(("Base" + class_name.title()), fields, eq=False)

        # Construct the final dataclass with the equality method
        built_classes[class_name] = dataclass(
            type(
                class_name.title(), (base_dc,), {"__eq__": make_eq_method(base_fields)}
            )
        )

    return built_classes


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
