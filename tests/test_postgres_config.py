from sqlark.postgres_config import PostgresConfig
from unittest.mock import patch


def test_initialize_with_dsn():
    dsn = "dbname=test user=postgres"
    pg_config = PostgresConfig(dsn=dsn)
    assert pg_config.connection_params == {"dsn": dsn}


@patch(
    "sqlark.postgres_config.get_secret",
    return_value={"username": "test-user", "password": "test-password"},
)
def test_initialize_with_rds_secret(get_secret):
    pg_config = PostgresConfig(
        aws_secret_name="test-secret", aws_region_name="us-west-2"
    )
    assert pg_config.connection_params == {
        "user": "test-user",
        "password": "test-password",
    }


@patch(
    "sqlark.postgres_config.get_secret",
    return_value={"username": "test-user", "password": "test-password"},
)
def test_initialize_with_rds_secret_and_dsn(get_secret):
    pg_config = PostgresConfig(
        aws_secret_name="test-secret", aws_region_name="us-west-2", dsn=None
    )

    assert pg_config.connection_params == {
        "user": "test-user",
        "password": "test-password",
    }
