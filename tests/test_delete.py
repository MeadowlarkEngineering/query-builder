from sqlark import Delete, PostgresConfig


def test_delete_01(pg_connection):
    """
    tests simple deletion
    """

    s = Delete(table_name="comments").where(column="id", operator="=", value=1)
    assert (
        s.to_sql(PostgresConfig()).as_string(pg_connection).strip()
        == 'DELETE FROM "comments" WHERE "comments"."id" = %s RETURNING *'
    )
    assert s.get_params() == [1]


def test_delete_02(pg_connection):
    """
    Tests sql injection
    """
    s = Delete(table_name="comments").where(
        column="id", operator="=", value="1; DROP TABLE comments"
    )
    assert (
        s.to_sql(PostgresConfig()).as_string(pg_connection).strip()
        == 'DELETE FROM "comments" WHERE "comments"."id" = %s RETURNING *'
    )
    assert s.get_params() == ["1; DROP TABLE comments"]


def test_delete_03(pg_connection):
    """
    Tests multiple where clause
    """
    s = (
        Delete(table_name="comments")
        .where(column="id", operator="=", value=1)
        .where_or(column="author", operator="=", value="John Doe")
    )
    assert (
        s.to_sql(PostgresConfig()).as_string(pg_connection).strip()
        == 'DELETE FROM "comments" WHERE "comments"."id" = %s OR ( "comments"."author" = %s ) RETURNING *'
    )
    assert s.get_params() == [1, "John Doe"]
