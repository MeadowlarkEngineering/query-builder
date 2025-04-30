from pytest import mark
from sqlark import utilities
from sqlark.column_definition import ColumnDefinition
from dataclasses import fields
from unittest import TestCase


@mark.parametrize(
    "row, expected",
    [
        ({"table_name.column_name": "value"}, {"table_name": {"column_name": "value"}}),
        (
            {
                "table_name.column_name": "value",
                "table_name.column2": "value2",
                "table_name2.column_name2": "value2",
            },
            {
                "table_name": {"column_name": "value", "column2": "value2"},
                "table_name2": {"column_name2": "value2"},
            },
        ),
        ({"column_name": "value"}, {"column_name": "value"}),
        (
            {"column_name": "value", "table_name.column_name": "value2"},
            {"column_name": "value", "table_name": {"column_name": "value2"}},
        ),
        (
            {
                "column_name": "value",
                "table_name.column_name": "value2",
                "table_name2.column_name2": "value3",
            },
            {
                "column_name": "value",
                "table_name": {"column_name": "value2"},
                "table_name2": {"column_name2": "value3"},
            },
        ),
    ],
)
def test_decompose_row(row, expected):
    TestCase().assertDictEqual(utilities.decompose_row(row), expected)


@mark.parametrize(
    "class_definitions",
    [
        (
            {
                "posts": [
                    ColumnDefinition("posts", "id", "integer", False, None),
                    ColumnDefinition("posts", "title", "text", False, None),
                    ColumnDefinition("posts", "body", "text", False, None),
                    ColumnDefinition(
                        "posts",
                        "created_at",
                        "timestamp without time zone",
                        False,
                        None,
                    ),
                ]
            }
        )
    ],
)
def test_build_simple_dataclasses(class_definitions):
    built = utilities.build_dataclasses(class_definitions)
    for table_name, columns in class_definitions.items():
        assert table_name in built
        assert built[table_name].__name__ == table_name.title()
        for column in columns:
            assert column.name in built[table_name].__annotations__
            assert (
                built[table_name].__annotations__[column.name]
                == utilities.POSTGRES_DATA_TYPES[column.data_type]
            )


@mark.parametrize(
    "class_definitions,values,equal",
    [
        (
            {
                "posts": [
                    ColumnDefinition("posts", "id", "integer", False, None),
                    ColumnDefinition("posts", "title", "text", False, None),
                ]
            },
            [
                {"posts": {"id": 1, "title": "test"}},
                {"posts": {"id": 1, "title": "test"}},
            ],
            True,
        ),
        (
            {
                "posts": [
                    ColumnDefinition("posts", "id", "integer", False, None),
                    ColumnDefinition("posts", "title", "text", False, None),
                    ColumnDefinition("posts", "author", "authors", False, None),
                ],
                "authors": [
                    ColumnDefinition("authors", "id", "integer", False, None),
                    ColumnDefinition("authors", "name", "text", False, None),
                ],
            },
            [
                {
                    "posts": {"id": 1, "title": "test"},
                    "authors": {"id": 1, "name": "Joe"},
                },
                {
                    "posts": {"id": 1, "title": "test"},
                    "authors": {"id": 1, "name": "Joe"},
                },
            ],
            True,
        ),
        (
            {
                "posts": [
                    ColumnDefinition("posts", "id", "integer", False, None),
                    ColumnDefinition("posts", "title", "text", False, None),
                    ColumnDefinition("posts", "author", "authors", False, None),
                    ColumnDefinition(
                        "posts", "comments", "comments", False, None, True
                    ),
                ],
                "comments": [
                    ColumnDefinition("comments", "id", "integer", False, None),
                    ColumnDefinition("comments", "post_id", "integer", False, None),
                    ColumnDefinition("comments", "body", "text", False, None),
                    ColumnDefinition("comments", "author", "authors", False, None),
                ],
                "authors": [
                    ColumnDefinition("authors", "id", "integer", False, None),
                    ColumnDefinition("authors", "name", "text", False, None),
                ],
            },
            [
                {
                    "posts": {"id": 1, "title": "test"},
                    "authors": {"id": 1, "name": "Joe"},
                    "comments": {"id": 1, "post_id": 1, "body": "test"},
                },
                {
                    "posts": {"id": 1, "title": "test"},
                    "authors": {"id": 2, "name": "Sue"},
                },
            ],
            True,
        ),
        (
            {
                "posts": [
                    ColumnDefinition("posts", "id", "integer", False, None),
                    ColumnDefinition("posts", "title", "text", False, None),
                    ColumnDefinition("posts", "author", "authors", False, None),
                ],
                "authors": [
                    ColumnDefinition("authors", "id", "integer", False, None),
                    ColumnDefinition("authors", "name", "text", False, None),
                ],
            },
            [
                {
                    "posts": {"id": 1, "title": "test"},
                    "authors": {"id": 1, "name": "Joe"},
                },
                {
                    "posts": {"id": 2, "title": "test2"},
                    "authors": {"id": 1, "name": "Joe"},
                },
            ],
            False,
        ),
        (
            {
                "posts": [
                    ColumnDefinition("posts", "id", "integer", False, None),
                    ColumnDefinition("posts", "title", "text", False, None),
                ]
            },
            [
                {"posts": {"id": 1, "title": "test"}},
                {"posts": {"id": 2, "title": "test"}},
            ],
            False,
        ),
    ],
)
def test_dataclass_equality(class_definitions, values, equal):
    built = utilities.build_dataclasses(class_definitions)
    Posts = built["posts"]
    posts1 = Posts(**values[0]["posts"])
    posts2 = Posts(**values[1]["posts"])
    if "authors" in built:
        Authors = built["authors"]
        posts1.author = Authors(**values[0]["authors"])
        posts2.author = Authors(**values[1]["authors"])

    assert (posts1 == posts2) == equal


@mark.parametrize(
    "class_definitions",
    [
        (
            {
                "posts": [
                    ColumnDefinition("posts", "id", "integer", False, None),
                    ColumnDefinition("posts", "title", "text", False, None),
                    ColumnDefinition("posts", "body", "text", False, None),
                    ColumnDefinition("posts", "author", "authors", False, None),
                    ColumnDefinition(
                        "posts", "comments", "comments", False, None, is_list=True
                    ),
                    ColumnDefinition(
                        "posts",
                        "created_at",
                        "timestamp without time zone",
                        False,
                        None,
                    ),
                ],
                "authors": [
                    ColumnDefinition("authors", "id", "integer", False, None),
                    ColumnDefinition("authors", "name", "text", False, None),
                    ColumnDefinition(
                        "authors",
                        "created_at",
                        "timestamp without time zone",
                        False,
                        None,
                    ),
                ],
                "comments": [
                    ColumnDefinition("comments", "id", "integer", False, None),
                    ColumnDefinition("comments", "post_id", "integer", False, None),
                    ColumnDefinition("comments", "body", "text", False, None),
                    ColumnDefinition("comments", "author", "authors", False, None),
                    ColumnDefinition(
                        "comments",
                        "created_at",
                        "timestamp without time zone",
                        False,
                        None,
                    ),
                ],
            }
        )
    ],
)
def test_build_complex_dataclasses(class_definitions):
    built = utilities.build_dataclasses(class_definitions)
    for table_name, columns in class_definitions.items():
        assert table_name in built
        assert built[table_name].__name__ == table_name.title()
        built_fields = fields(built[table_name])
        built_field_names = [f.name for f in built_fields]
        for column in columns:
            assert column.name in built_field_names
            f = built_fields[built_field_names.index(column.name)]
            if column.is_list:
                assert f.type.__origin__ == list
            if column.data_type in utilities.POSTGRES_DATA_TYPES:
                assert f.type == utilities.POSTGRES_DATA_TYPES[column.data_type]
