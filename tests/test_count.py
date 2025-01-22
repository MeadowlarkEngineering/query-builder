"""
Test count builder
"""
from query_builder.count import Count

def test_count_01(pg_connection):
    count = Count("table_name")
    assert count.to_sql(pg_connection).as_string(pg_connection).strip() == 'SELECT COUNT(*) as "table_name.count" FROM "table_name"'

def test_count_02(pg_connection):
    count = Count("table_name")
    count.group_by("c1")
    assert count.to_sql(pg_connection).as_string(pg_connection).strip() == 'SELECT COUNT(*) as "table_name.count","table_name"."c1" as "table_name.c1" FROM "table_name"    GROUP BY "table_name"."c1"'

def test_count_03(pg_connection):
    count = Count("table_name")
    count.group_by("c1", "c2")
    assert count.to_sql(pg_connection).as_string(pg_connection).strip() == 'SELECT COUNT(*) as "table_name.count","table_name"."c1" as "table_name.c1","table_name"."c2" as "table_name.c2" FROM "table_name"    GROUP BY "table_name"."c1","table_name"."c2"'

def test_count_04(pg_connection):
    count = Count("table_name")
    count.group_by("c1", "c2")
    count.where(column="x", operator="=", value=1)
    assert count.to_sql(pg_connection).as_string(pg_connection).strip() == 'SELECT COUNT(*) as "table_name.count","table_name"."c1" as "table_name.c1","table_name"."c2" as "table_name.c2" FROM "table_name"   WHERE "table_name"."x" = %s  GROUP BY "table_name"."c1","table_name"."c2"'
    assert count.get_params() == [1]

def test_count_05(pg_connection):
    count = Count("table1")
    count.group_by("c1", "c2")
    count.join(right_table="table2", left_col="id", right_col="table1_id")
    assert count.to_sql(pg_connection).as_string(pg_connection).strip() == 'SELECT COUNT(*) as "table1.count","table1"."c1" as "table1.c1","table1"."c2" as "table1.c2" FROM "table1" INNER JOIN "table2" ON "table1"."id" = "table2"."table1_id"    GROUP BY "table1"."c1","table1"."c2"'