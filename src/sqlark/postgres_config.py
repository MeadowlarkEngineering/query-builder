"""
Postgres Configuration
"""

import time
from contextlib import contextmanager
import json
import psycopg2
from psycopg2.extras import DictCursor
import boto3
from botocore.exceptions import ClientError


cached_secret = None
cache_expiration_seconds = 120


def get_secret(secret_name, region_name) -> dict:
    """
    Returns a dictionary with {username, password} for
    """
    # pylint: disable=global-statement
    global cached_secret
    if cached_secret is not None and cached_secret["expiration"] > time.time():
        return cached_secret["secret"]

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    secret = get_secret_value_response["SecretString"]
    cached_secret = {
        "secret": json.loads(secret),
        "expiration": time.time() + cache_expiration_seconds,
    }

    return cached_secret["secret"]


class PostgresConfig:
    """
    Configurations required for the Postgres client.
    There are multiple ways to specify the configuration.

    1. Using a DSN string
        - dsn
    2. Using individual parameters for each configuration value
        - dbname
        - user
        - password
        - host
        - port (optional)
    3. Using AWS Secrets Manager to store the username and password
        - aws_secret_name
        - aws_region_name
        - dname
        - host
        - port (optional)
    """

    # pylint: disable=too-many-instance-attributes
    def __init__(
        self,
        aws_secret_name: str | None = None,
        aws_region_name: str | None = None,
        dbname: str | None = None,
        user: str | None = None,
        password: str | None = None,
        host: str | None = None,
        port: str | None = None,
        dsn: str | None = None,
    ):
        """Configuration values for the Postgres client."""
        self.dbname = dbname
        self.aws_secret_name = aws_secret_name
        self.aws_region_name = aws_region_name
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.dsn = dsn

    @property
    def connection_params(self):
        """Parameters for connecting to postgres database"""
        if self.dsn is not None:
            return {"dsn": self.dsn}

        params = {}

        if self.aws_secret_name is not None and self.aws_region_name is not None:
            secret = get_secret(self.aws_secret_name, self.aws_region_name)
            params["user"] = secret["username"]
            params["password"] = secret["password"]

        if self.dbname is not None:
            params["dbname"] = self.dbname
        if self.user is not None:
            params["user"] = self.user
        if self.password is not None:
            params["password"] = self.password
        if self.host is not None:
            params["host"] = self.host
        if self.port is not None:
            params["port"] = self.port
        return params

    def register_adapters(self):
        """Register custom adapters"""
        # pylint: disable=import-outside-toplevel
        from psycopg2.extras import Json
        from psycopg2.extensions import register_adapter

        register_adapter(dict, Json)
        register_adapter(list, Json)

    @contextmanager
    def connect_with_cursor(self, transactional=False):
        """Connect to database"""
        with psycopg2.connect(**self.connection_params) as connection:
            if not transactional:
                connection.set_session(autocommit=True)

            with connection.cursor(cursor_factory=DictCursor) as cursor:
                yield cursor
