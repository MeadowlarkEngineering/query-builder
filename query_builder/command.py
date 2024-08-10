"""
Abstract SQL command class
"""

from abc import ABC, abstractmethod
import psycopg2
from query_builder.postgres_config import PostgresConfig
from query_builder.utilities import get_logger
from query_builder import response_formatters

class SQLCommand(ABC):
    """
    Abstract SQL command class.  Subclasses must implement the to_sql and execute methods
    """
    __slots__ = [
        "logger",
        "_table_name",
        "_where",
        "_response_formatter"]
    
    def __init__(self):
        self.logger = get_logger(__name__)

        # Default response is a list of dictionaries
        self._response_formatter = response_formatters.default_response_formatter

    @abstractmethod
    def to_sql(self, pg_config: PostgresConfig) -> psycopg2.sql.SQL:
        """
        Returns the SQL representation of the command
        """
        raise NotImplementedError

    @abstractmethod
    def execute(self, pg_config: PostgresConfig):
        """
        Executes the command
        """
        raise NotImplementedError

    def respond_with_decomposed_dict(self):
        """
        Respond to execute() with a dictionary of dictionaries.
        The outer dictionary is keyed by table name.
        The inner dictionaries are the columns of the table.
        """
        self._response_formatter = response_formatters.decompose_dict_response_formatter
        return self
    
    def respond_with_object(self):
        """
        Respond to execute() with an object constructed from the result
        There is one object per row.

        If the query does not have a join, the object will have attributes for each column in the table.

        If the query has a join, the object will have attributes for each table joined in the query.
        Each attribute is a class with attributes for each column in the table.

        Example query without join:
        Select("posts").respond_with_object().execute()

        The result will be a list of objects with the following structure:
        [
            Posts(id=1, title="Post 1"),
            Posts(id=2, title="Post 2")
        ]

        Example query with join:
        Select("posts").join("comments").respond_with_object().execute()

        The result will be a list of objects with the following structure:
        [
            Row(
                posts=Posts(id=1, title="Post 1"),
                comments=Comments(id=1, post_id=1, comment="Comment 1")
            ),
            Row(
                posts=Posts(id=1, title="Post 1"),
                comments=Comments(id=2, post_id=1, comment="Comment 2")
            )
        ]
        """


        self._response_formatter = response_formatters.object_response_formatter
        return self
