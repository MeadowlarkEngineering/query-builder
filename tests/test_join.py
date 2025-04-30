from sqlark import Join


def test_init_with_kwargs(pg_connection):
    """
    tests simple initialization
    """

    j = Join(
        left_table="comments", right_table="posts", left_col="post_id", right_col="id"
    )

    assert (
        j.sql.as_string(pg_connection)
        == 'INNER JOIN "posts" ON "comments"."post_id" = "posts"."id" '
    )
    assert j.tables == ["posts"]


def test_init_with_join(pg_connection):
    """
    Tests initialization with a join
    """

    j1 = Join(
        left_table="comments", right_table="posts", left_col="post_id", right_col="id"
    )
    j = Join(j1)

    assert (
        j.sql.as_string(pg_connection)
        == 'INNER JOIN "posts" ON "comments"."post_id" = "posts"."id" '
    )
    assert j.tables == ["posts"]


def test_multiple_join(pg_connection):
    """
    tests builder pattern
    """

    j = Join(
        left_table="comments", right_table="posts", left_col="post_id", right_col="id"
    ).join(
        left_table="comments",
        right_table="authors",
        left_col="author_id",
        right_col="id",
    )

    assert (
        j.sql.as_string(pg_connection)
        == 'INNER JOIN "posts" ON "comments"."post_id" = "posts"."id" INNER JOIN "authors" ON "comments"."author_id" = "authors"."id" '
    )
    assert j.tables == ["posts", "authors"]


def test_join_on(pg_connection):
    """
    tests join on
    """

    j = Join(right_table="posts", on="comments.post_id = posts.id")

    assert (
        j.sql.as_string(pg_connection)
        == 'INNER JOIN "posts" ON comments.post_id = posts.id '
    )
    assert j.tables == ["posts"]
