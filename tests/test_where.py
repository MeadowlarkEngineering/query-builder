import pytest
from psycopg2 import sql
from sqlark.where import Where


def test_initialize_with_kwargs(pg_connection):
    w = Where(table="posts", column="author", operator="=", value="Clark Kent")
    assert w.sql.as_string(pg_connection) == '"posts"."author" = %s'
    assert w.params == ["Clark Kent"]


def test_raises_with_missing_kwargs():
    with pytest.raises(AttributeError):
        Where(column="author", operator="=", value="Clark Kent")
    with pytest.raises(AttributeError):
        Where(table="posts", operator="=", value="Clark Kent")
    with pytest.raises(AttributeError):
        Where(table="posts", column="author", value="Clark Kent")
    with pytest.raises(AttributeError):
        Where(table="posts", column="author", operator="=")


def test_initialize_with_sql_values(pg_connection):
    w = Where(sql.SQL('"posts"."author" = %s'), ["Clark Kent"])
    assert w.sql.as_string(pg_connection) == '"posts"."author" = %s'
    assert w.params == ["Clark Kent"]


def test_sql_and(pg_connection):
    w = Where(sql.SQL('"posts"."author" = %s'), ["Clark Kent"]).sql_and(
        table="posts", column="created_at", operator=">", value="2023-04-14"
    )

    assert (
        w.sql.as_string(pg_connection)
        == '"posts"."author" = %s AND "posts"."created_at" > %s'
    )
    assert w.params == ["Clark Kent", "2023-04-14"]


def test_sql_or(pg_connection):
    w = Where(sql.SQL('"posts"."author" = %s'), ["Clark Kent"]).sql_or(
        table="posts", column="created_at", operator=">", value="2023-04-14"
    )

    assert (
        w.sql.as_string(pg_connection)
        == '"posts"."author" = %s OR "posts"."created_at" > %s'
    )
    assert w.params == ["Clark Kent", "2023-04-14"]


def test_sql_and_or(pg_connection):
    w = (
        Where(sql.SQL('"posts"."author" = %s'), ["Clark Kent"])
        .sql_or(table="posts", column="created_at", operator=">", value="2023-04-14")
        .sql_and(table="posts", column="text", operator="like", value="%up and away%")
    )

    assert (
        w.sql.as_string(pg_connection)
        == '"posts"."author" = %s OR "posts"."created_at" > %s AND "posts"."text" like %s'
    )
    assert w.params == ["Clark Kent", "2023-04-14", "%up and away%"]


def test_sql_and_grouped_or(pg_connection):
    w = Where(sql.SQL('"posts"."author" = %s'), ["Clark Kent"]).sql_and(
        Where(
            table="posts", column="created_at", operator=">", value="2023-04-14"
        ).sql_or(table="posts", column="text", operator="like", value="%up and away%")
    )

    assert (
        w.sql.as_string(pg_connection)
        == '"posts"."author" = %s AND ( "posts"."created_at" > %s OR "posts"."text" like %s )'
    )
    assert w.params == ["Clark Kent", "2023-04-14", "%up and away%"]


def test_sql_or_grouped_and(pg_connection):
    w = Where(sql.SQL('"posts"."author" = %s'), ["Clark Kent"]).sql_or(
        Where(
            table="posts", column="created_at", operator=">", value="2023-04-14"
        ).sql_and(table="posts", column="text", operator="like", value="%up and away%")
    )

    assert (
        w.sql.as_string(pg_connection)
        == '"posts"."author" = %s OR ( "posts"."created_at" > %s AND "posts"."text" like %s )'
    )
    assert w.params == ["Clark Kent", "2023-04-14", "%up and away%"]
