"""
Unit testing for Select SQLCommand
"""

from sqlark import Update, PostgresConfig


def test_update_01(pg_connection):
    """
    tests simple initialization
    """

    s = (
        Update(table_name="comments")
        .set(values={"author": "John Doe", "body": "Hello World"})
        .where(column="id", operator="=", value=1)
    )
    assert (
        s.to_sql(PostgresConfig()).as_string(pg_connection).strip()
        == 'UPDATE "comments" SET "author"=\'John Doe\',"body"=\'Hello World\'  WHERE "comments"."id" = %s RETURNING *'
    )
    assert s.get_params() == [1]


def test_update_02(pg_connection):
    """
    Tests sql injection
    """
    s = (
        Update(table_name="comments")
        .set(values={"author": "John Doe", "body": "Hello World"})
        .where(column="id", operator="=", value="1; DROP TABLE comments")
    )
    assert (
        s.to_sql(PostgresConfig()).as_string(pg_connection).strip()
        == 'UPDATE "comments" SET "author"=\'John Doe\',"body"=\'Hello World\'  WHERE "comments"."id" = %s RETURNING *'
    )
    assert s.get_params() == ["1; DROP TABLE comments"]


def test_increment(pg_connection):
    """
    tests incrementing a column
    """

    s = (
        Update(table_name="comments")
        .increment(column="likes", value=1)
        .where(column="id", operator="=", value=1)
    )
    assert (
        s.to_sql(PostgresConfig()).as_string(pg_connection).strip()
        == 'UPDATE "comments" SET "likes"="likes" + 1  WHERE "comments"."id" = %s RETURNING *'
    )
    assert s.get_params() == [1]
