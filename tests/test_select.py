"""
Unit testing for Select SQLCommand
"""

from unittest import mock
from sqlark import Select, Where, Join, PostgresConfig, ColumnDefinition


def mock_column_definitions(*args):
    """
    Mock function to return column definitions
    """

    def mock_get_columns(table_name, pg_config, use_cache):
        return [
            ColumnDefinition(
                table_name=table_name,
                name=arg,
                data_type="text",
                is_nullable=True,
                default=None,
                function=None,
                alias=None,
            )
            for arg in args
        ]

    return mock_get_columns


@mock.patch(
    "sqlark.utilities.get_column_definitions",
    side_effect=mock_column_definitions("author", "body"),
)
def test_select_01(patch, pg_connection):
    """
    tests simple initialization
    """

    s = Select(table_name="comments")
    assert (
        s.to_sql(PostgresConfig()).as_string(pg_connection).strip()
        == 'SELECT "comments"."author" as "comments.author","comments"."body" as "comments.body" FROM "comments"'
    )
    assert s.get_params() == []


@mock.patch(
    "sqlark.utilities.get_column_definitions",
    side_effect=mock_column_definitions("author", "body"),
)
def test_select_02(patch, pg_connection):
    """
    tests select with where clause
    """

    s = Select(table_name="comments").where(
        Where(table="comments", column="author", operator="=", value="Clark Kent")
    )
    assert (
        s.to_sql(PostgresConfig()).as_string(pg_connection).strip()
        == 'SELECT "comments"."author" as "comments.author","comments"."body" as "comments.body" FROM "comments"   WHERE "comments"."author" = %s'
    )
    assert s.get_params() == ["Clark Kent"]


@mock.patch(
    "sqlark.utilities.get_column_definitions",
    side_effect=mock_column_definitions("author", "body"),
)
def test_select_02a(patch, pg_connection):
    """
    tests select with where clause using kwargs
    """

    s = Select(table_name="comments").where(
        table="comments", column="author", operator="=", value="Clark Kent"
    )
    assert (
        s.to_sql(PostgresConfig()).as_string(pg_connection).strip()
        == 'SELECT "comments"."author" as "comments.author","comments"."body" as "comments.body" FROM "comments"   WHERE "comments"."author" = %s'
    )
    assert s.get_params() == ["Clark Kent"]


@mock.patch(
    "sqlark.utilities.get_column_definitions",
    side_effect=mock_column_definitions("author", "body"),
)
def test_select_03(patch, pg_connection):
    """
    tests select with where clause and limit
    """

    s = (
        Select(table_name="comments")
        .where(
            Where(table="comments", column="author", operator="=", value="Clark Kent")
        )
        .limit(10)
    )
    assert (
        s.to_sql(PostgresConfig()).as_string(pg_connection).strip()
        == 'SELECT "comments"."author" as "comments.author","comments"."body" as "comments.body" FROM "comments"   WHERE "comments"."author" = %s    LIMIT 10'
    )
    assert s.get_params() == ["Clark Kent"]


@mock.patch(
    "sqlark.utilities.get_column_definitions",
    side_effect=mock_column_definitions("author", "body"),
)
def test_select_04(patch, pg_connection):
    """
    tests select with where clause, limit, and offset
    """

    s = (
        Select(table_name="comments")
        .where(
            Where(table="comments", column="author", operator="=", value="Clark Kent")
        )
        .limit(10)
        .offset(5)
    )
    assert (
        s.to_sql(PostgresConfig()).as_string(pg_connection).strip()
        == 'SELECT "comments"."author" as "comments.author","comments"."body" as "comments.body" FROM "comments"   WHERE "comments"."author" = %s   OFFSET 5 LIMIT 10'
    )
    assert s.get_params() == ["Clark Kent"]


@mock.patch(
    "sqlark.utilities.get_column_definitions",
    side_effect=mock_column_definitions("author", "body"),
)
def test_select_05a(patch, pg_connection):
    """
    tests select with where clause, limit, offset, and order by
    """

    s = (
        Select(table_name="comments")
        .where(
            Where(table="comments", column="author", operator="=", value="Clark Kent")
        )
        .limit(10)
        .offset(5)
        .order_by("author")
    )
    assert (
        s.to_sql(PostgresConfig()).as_string(pg_connection).strip()
        == 'SELECT "comments"."author" as "comments.author","comments"."body" as "comments.body" FROM "comments"   WHERE "comments"."author" = %s ORDER BY "comments"."author" ASC  OFFSET 5 LIMIT 10'
    )
    assert s.get_params() == ["Clark Kent"]


@mock.patch(
    "sqlark.utilities.get_column_definitions",
    side_effect=mock_column_definitions("author", "body"),
)
def test_select_05b(patch, pg_connection):
    """
    tests select with where clause, limit, offset, and order by
    """

    s = (
        Select(table_name="comments")
        .where(
            Where(table="comments", column="author", operator="=", value="Clark Kent")
        )
        .limit(10)
        .offset(5)
        .order_by("author")
        .group_by("author")
    )
    assert (
        s.to_sql(PostgresConfig()).as_string(pg_connection).strip()
        == 'SELECT "comments"."author" as "comments.author","comments"."body" as "comments.body" FROM "comments"   WHERE "comments"."author" = %s ORDER BY "comments"."author" ASC GROUP BY "comments"."author" OFFSET 5 LIMIT 10'
    )
    assert s.get_params() == ["Clark Kent"]


@mock.patch(
    "sqlark.utilities.get_column_definitions",
    side_effect=mock_column_definitions("id", "author", "body"),
)
def test_select_06(patch, pg_connection):
    """
    tests select with join where clause, limit, offset, order by
    """

    j = Join(
        left_table="comments",
        right_table="other_comments",
        left_col="id",
        right_col="id",
    )
    s = (
        Select(table_name="comments")
        .join(join=j)
        .where(
            Where(table="comments", column="author", operator="=", value="Clark Kent")
        )
        .limit(10)
        .offset(5)
        .order_by("author")
    )
    assert s.to_sql(PostgresConfig()).as_string(pg_connection).strip() == (
        'SELECT "comments"."id" as "comments.id","comments"."author" as "comments.author",'
        + '"comments"."body" as "comments.body","other_comments"."id" as "other_comments.id",'
        + '"other_comments"."author" as "other_comments.author","other_comments"."body" as "other_comments.body"'
        + ' FROM "comments" INNER JOIN "other_comments" ON "comments"."id" = "other_comments"."id"'
        + '   WHERE "comments"."author" = %s ORDER BY "comments"."author" ASC  OFFSET 5 LIMIT 10'
    )
    assert s.get_params() == ["Clark Kent"]


@mock.patch(
    "sqlark.utilities.get_column_definitions",
    side_effect=mock_column_definitions("id", "author", "body"),
)
def test_select_07(patch, pg_connection):
    """
    tests select with join where clause, limit, offset, order by
    """

    s = (
        Select(table_name="comments")
        .join(
            left_table="comments",
            right_table="other_comments",
            left_col="id",
            right_col="id",
        )
        .where(
            Where(table="comments", column="author", operator="=", value="Clark Kent")
        )
        .limit(10)
        .offset(5)
        .order_by("author")
    )
    assert s.to_sql(PostgresConfig()).as_string(pg_connection).strip() == (
        'SELECT "comments"."id" as "comments.id","comments"."author" as "comments.author",'
        + '"comments"."body" as "comments.body","other_comments"."id" as "other_comments.id",'
        + '"other_comments"."author" as "other_comments.author","other_comments"."body" as "other_comments.body"'
        + ' FROM "comments" INNER JOIN "other_comments" ON "comments"."id" = "other_comments"."id"'
        + '   WHERE "comments"."author" = %s ORDER BY "comments"."author" ASC  OFFSET 5 LIMIT 10'
    )
    assert s.get_params() == ["Clark Kent"]


@mock.patch(
    "sqlark.utilities.get_column_definitions",
    side_effect=mock_column_definitions("id", "author", "body"),
)
def test_select_08(patch, pg_connection):
    """
    tests select with join where clause, limit, offset, order by
    """

    s = (
        Select(table_name="comments")
        .join(
            left_table="comments",
            right_table="other_comments",
            left_col="id",
            right_col="id",
        )
        .where(
            Where(table="comments", column="author", operator="=", value="Clark Kent")
        )
        .limit(10)
        .offset(5)
        .order_by("author", table="other_comments")
    )
    assert s.to_sql(PostgresConfig()).as_string(pg_connection).strip() == (
        'SELECT "comments"."id" as "comments.id","comments"."author" as "comments.author",'
        + '"comments"."body" as "comments.body","other_comments"."id" as "other_comments.id",'
        + '"other_comments"."author" as "other_comments.author","other_comments"."body" as "other_comments.body"'
        + ' FROM "comments" INNER JOIN "other_comments" ON "comments"."id" = "other_comments"."id"'
        + '   WHERE "comments"."author" = %s ORDER BY "other_comments"."author" ASC  OFFSET 5 LIMIT 10'
    )
    assert s.get_params() == ["Clark Kent"]


@mock.patch(
    "sqlark.utilities.get_column_definitions",
    side_effect=mock_column_definitions("id", "author", "body"),
)
def test_select_09(patch, pg_connection):
    j1 = Join(
        left_table="posts", right_table="comments", left_col="id", right_col="post_id"
    )
    j2 = Join(
        left_table="comments",
        right_table="authors",
        left_col="author_id",
        right_col="id",
    )
    s = Select(table_name="posts").join(j1).join(j2)

    assert s.to_sql(PostgresConfig()).as_string(pg_connection).strip() == (
        'SELECT "posts"."id" as "posts.id","posts"."author" as "posts.author",'
        + '"posts"."body" as "posts.body","comments"."id" as "comments.id",'
        + '"comments"."author" as "comments.author","comments"."body" as "comments.body",'
        + '"authors"."id" as "authors.id","authors"."author" as "authors.author","authors"."body" as "authors.body"'
        + ' FROM "posts" INNER JOIN "comments" ON "posts"."id" = "comments"."post_id"'
        + ' INNER JOIN "authors" ON "comments"."author_id" = "authors"."id"'
    )


@mock.patch(
    "sqlark.utilities.get_column_definitions",
    side_effect=mock_column_definitions("id", "author", "body"),
)
def test_select_10(patch, pg_connection):
    s = (
        Select(table_name="posts")
        .join(
            left_table="posts",
            right_table="comments",
            left_col="id",
            right_col="post_id",
        )
        .join(
            left_table="comments",
            right_table="authors",
            left_col="author_id",
            right_col="id",
        )
    )

    assert s.to_sql(PostgresConfig()).as_string(pg_connection).strip() == (
        'SELECT "posts"."id" as "posts.id","posts"."author" as "posts.author",'
        + '"posts"."body" as "posts.body","comments"."id" as "comments.id",'
        + '"comments"."author" as "comments.author","comments"."body" as "comments.body",'
        + '"authors"."id" as "authors.id","authors"."author" as "authors.author","authors"."body" as "authors.body"'
        + ' FROM "posts" INNER JOIN "comments" ON "posts"."id" = "comments"."post_id"'
        + ' INNER JOIN "authors" ON "comments"."author_id" = "authors"."id"'
    )


@mock.patch(
    "sqlark.utilities.get_column_definitions",
    side_effect=mock_column_definitions("author", "body"),
)
def test_select_11(patch, pg_connection):
    """
    tests select with multiple where clause
    """

    s = (
        Select(table_name="comments")
        .where(column="author", operator="=", value="Clark Kent")
        .where_and(column="id", operator=">", value=5)
    )

    assert (
        s.to_sql(PostgresConfig()).as_string(pg_connection).strip()
        == 'SELECT "comments"."author" as "comments.author","comments"."body" as "comments.body" FROM "comments"   '
        + 'WHERE "comments"."author" = %s AND ( "comments"."id" > %s )'
    )
    assert s.get_params() == ["Clark Kent", 5]


@mock.patch(
    "sqlark.utilities.get_column_definitions",
    side_effect=mock_column_definitions("author", "body"),
)
def test_select_12(patch, pg_connection):
    """
    tests select with multiple where clause
    """

    s = (
        Select(table_name="comments")
        .where(column="author", operator="=", value="Clark Kent")
        .where_or(column="id", operator=">", value=5)
    )

    assert (
        s.to_sql(PostgresConfig()).as_string(pg_connection).strip()
        == 'SELECT "comments"."author" as "comments.author","comments"."body" as "comments.body" FROM "comments"   '
        + 'WHERE "comments"."author" = %s OR ( "comments"."id" > %s )'
    )
    assert s.get_params() == ["Clark Kent", 5]


@mock.patch(
    "sqlark.utilities.get_column_definitions",
    side_effect=mock_column_definitions("author", "body"),
)
def test_select_12a(patch, pg_connection):
    """
    tests select with multiple where clause
    """

    s = (
        Select(table_name="comments")
        .where(column="author", operator="=", value="Clark Kent")
        .where_and(column="id", operator=">", value=10)
        .where_or(column="id", operator="<", value=5)
    )

    assert (
        s.to_sql(PostgresConfig()).as_string(pg_connection).strip()
        == 'SELECT "comments"."author" as "comments.author","comments"."body" as "comments.body" FROM "comments"   '
        + 'WHERE "comments"."author" = %s AND ( "comments"."id" > %s ) OR ( "comments"."id" < %s )'
    )
    assert s.get_params() == ["Clark Kent", 10, 5]


@mock.patch(
    "sqlark.utilities.get_column_definitions",
    side_effect=mock_column_definitions("author", "body"),
)
def test_select_12b(patch, pg_connection):
    """
    tests select with multiple where clause
    """

    s = (
        Select(table_name="comments")
        .where(column="author", operator="=", value="Clark Kent")
        .where_and(
            Where(table="comments", column="id", operator=">", value=10).sql_or(
                table="comments", column="id", operator="<", value=5
            )
        )
    )

    assert (
        s.to_sql(PostgresConfig()).as_string(pg_connection).strip()
        == 'SELECT "comments"."author" as "comments.author","comments"."body" as "comments.body" FROM "comments"   '
        + 'WHERE "comments"."author" = %s AND ( "comments"."id" > %s OR "comments"."id" < %s )'
    )
    assert s.get_params() == ["Clark Kent", 10, 5]


@mock.patch(
    "sqlark.utilities.get_column_definitions",
    side_effect=mock_column_definitions("author", "body"),
)
def test_select_13a(patch, pg_connection):
    """
    Tests distinct
    """
    s = Select("comments").distinct("author")
    assert (
        s.to_sql(PostgresConfig()).as_string(pg_connection).strip()
        == 'SELECT DISTINCT "author" FROM "comments"'
    )


@mock.patch(
    "sqlark.utilities.get_column_definitions",
    side_effect=mock_column_definitions("author", "body", "date"),
)
def test_select_13b(patch, pg_connection):
    """
    Tests distinct
    """
    s = Select("comments").distinct(["author", "date"])
    assert (
        s.to_sql(PostgresConfig()).as_string(pg_connection).strip()
        == 'SELECT DISTINCT "author", "date" FROM "comments"'
    )


@mock.patch(
    "sqlark.utilities.get_column_definitions",
    side_effect=mock_column_definitions("id", "author", "body"),
)
def test_select_14(patch, pg_connection):
    """
    Tests where_in
    """
    s = Select("comments").where(column="id", operator="IN", value=[1, 2, 3, 4])
    assert (
        s.to_sql(PostgresConfig()).as_string(pg_connection).strip()
        == 'SELECT "comments"."id" as "comments.id","comments"."author" as "comments.author","comments"."body" as "comments.body" FROM "comments"   WHERE "comments"."id" IN %s'
    )
    assert s.get_params() == [[1, 2, 3, 4]]


@mock.patch(
    "sqlark.utilities.get_column_definitions",
    side_effect=mock_column_definitions("id", "author", "body"),
)
def test_select_15(patch, pg_connection):
    """
    tests select with join where clause, multiple order by
    """

    s = (
        Select(table_name="comments")
        .join(
            left_table="comments",
            right_table="other_comments",
            left_col="id",
            right_col="id",
        )
        .where(
            Where(table="comments", column="author", operator="=", value="Clark Kent")
        )
        .order_by(["author", "body"])
    )
    assert s.to_sql(PostgresConfig()).as_string(pg_connection).strip() == (
        'SELECT "comments"."id" as "comments.id","comments"."author" as "comments.author",'
        + '"comments"."body" as "comments.body","other_comments"."id" as "other_comments.id",'
        + '"other_comments"."author" as "other_comments.author","other_comments"."body" as "other_comments.body"'
        + ' FROM "comments" INNER JOIN "other_comments" ON "comments"."id" = "other_comments"."id"'
        + '   WHERE "comments"."author" = %s ORDER BY "comments"."author" ASC, "comments"."body" ASC'
    )
    assert s.get_params() == ["Clark Kent"]
