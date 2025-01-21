# Query Builder

A lightweight wrapper around psycopg2 for creating queries using a builder pattern.

Example Query:


## Getting Started

### Installation

Using pip
```sh
pip install git+https://github.com/MeadowlarkEngineering/query-builder.git#egg=query-builder
```

Using poetry
```sh
poetry add git+https://github.com/MeadowlarkEngineering/query-builder.git
```

### Usage

#### Select

Select everything from a table.

```python
from query_builder import PostgresConfig, Select
config = PostgresConfig(dbname="blog", user="postgres-username", password="postgres-password)
Select("comments").execute(config)
> [{'id': 1, 'text': "A comment"}]
```

Add joins, multiple where clauses, offsets, and limits.

```python
s = Select(table_name="posts").\
    join(left_table="posts", right_table="authors", left_col="author_id", right_col="id").\
    where(table="authors", column="id", operator="=", value=1).\
    where_and(table="authors", column="created_at", operator=">", value="2024-01-01").\
    where_and(table="authors", column="created_at", operator=">", value="2024-01-01").\
    limit(10).\
    offset(5).\
    order_by("created_at", table="posts")
result = s.execute(config)
```

Insert data
```python
i = Insert(table_name="posts").values([{"author_id": 1, "body": "this is a post"}]).on_conflict('id', 'update')
result = i.execute(config)
```

## Development
```sh
pip3 install --upgrade pip poetry
poetry self add "poetry-dynamic-versioning[plugin]"
poetry install
```

## Unit Testing

Start a postgres database. The tests don't modify the database, but do require an active psycopg2 connection.

```
docker run -d -e POSTGRES_PASSWORD=postgres -p 5432:5432 postgres
```

Run the unit tests
```
poetry run pytest
```
You may need to set PGUSER, PGDATABASE, and PGPASSWORD environment variables to establish the connection

Copyright 2024 - Meadowlark Engineering