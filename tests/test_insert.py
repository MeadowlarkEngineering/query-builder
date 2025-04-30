"""
Unit testing for Insert SQLCommand
"""

from sqlark import Insert, PostgresConfig


def test_insert_01(pg_connection):
    """
    tests simple initialization
    """

    s = Insert(table_name="comments").values(
        [{"author": "Clark Kent", "body": "Up and away!"}]
    )
    assert (
        s.to_sql(PostgresConfig()).as_string(pg_connection).strip()
        == 'INSERT INTO "comments" ("author","body") VALUES %s  RETURNING *'
    )


def test_insert_02(pg_connection):
    """
    tests insert with on conflict
    """

    s = (
        Insert(table_name="comments")
        .values([{"author": "Clark Kent", "body": "Up and away!"}])
        .on_conflict("author", "nothing")
    )
    assert (
        s.to_sql(PostgresConfig()).as_string(pg_connection).strip()
        == 'INSERT INTO "comments" ("author","body") VALUES %s ON CONFLICT ("author") DO NOTHING RETURNING *'
    )


def test_insert_03a(pg_connection):
    """
    tests insert with on conflict and update
    """

    s = (
        Insert(table_name="comments")
        .values([{"author": "Clark Kent", "body": "Up and away!"}])
        .on_conflict("author", "update")
    )
    assert (
        s.to_sql(PostgresConfig()).as_string(pg_connection).strip()
        == 'INSERT INTO "comments" ("author","body") VALUES %s ON CONFLICT ("author") DO UPDATE SET "author" = COALESCE(EXCLUDED."author", "comments"."author"),"body" = COALESCE(EXCLUDED."body", "comments"."body") RETURNING *'
    )


def test_insert_03b(pg_connection):
    """
    tests insert with on conflict and update
    """

    s = (
        Insert(table_name="comments")
        .values([{"author": "Clark Kent", "body": "Up and away!"}])
        .on_conflict(["author", "body"], "update")
    )
    assert (
        s.to_sql(PostgresConfig()).as_string(pg_connection).strip()
        == 'INSERT INTO "comments" ("author","body") VALUES %s ON CONFLICT ("author","body") DO UPDATE SET "author" = COALESCE(EXCLUDED."author", "comments"."author"),"body" = COALESCE(EXCLUDED."body", "comments"."body") RETURNING *'
    )


def test_insert_04(pg_connection):
    """
    tests insert with on conflict and update
    """

    s = (
        Insert(table_name="comments")
        .values({"author": "Clark Kent", "body": "Up and away!"})
        .on_conflict(["author", "body"], "update")
    )
    assert (
        s.to_sql(PostgresConfig()).as_string(pg_connection).strip()
        == 'INSERT INTO "comments" ("author","body") VALUES %s ON CONFLICT ("author","body") DO UPDATE SET "author" = COALESCE(EXCLUDED."author", "comments"."author"),"body" = COALESCE(EXCLUDED."body", "comments"."body") RETURNING *'
    )
