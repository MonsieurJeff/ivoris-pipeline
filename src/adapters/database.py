"""
SQL Server Database Adapter.

Provides connection management and query execution for the Ivoris DentalDB.
"""

import logging
from contextlib import contextmanager
from typing import Generator, Any

import pyodbc

logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Database operation error."""
    pass


class DatabaseAdapter:
    """SQL Server database connection adapter."""

    def __init__(
        self,
        host: str,
        port: int,
        database: str,
        user: str,
        password: str,
        driver: str = "ODBC Driver 18 for SQL Server"
    ):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.driver = driver
        self._connection: pyodbc.Connection | None = None

    @property
    def connection_string(self) -> str:
        """Build ODBC connection string."""
        return (
            f"DRIVER={{{self.driver}}};"
            f"SERVER={self.host},{self.port};"
            f"DATABASE={self.database};"
            f"UID={self.user};"
            f"PWD={self.password};"
            f"TrustServerCertificate=yes;"
        )

    def connect(self) -> None:
        """Establish database connection."""
        if self._connection is not None:
            return

        try:
            logger.debug(f"Connecting to {self.database}...")
            self._connection = pyodbc.connect(self.connection_string)
            logger.info(f"Connected to {self.database}")
        except pyodbc.Error as e:
            logger.error(f"Connection failed: {e}")
            raise DatabaseError(f"Connection failed: {e}") from e

    def disconnect(self) -> None:
        """Close database connection."""
        if self._connection is not None:
            self._connection.close()
            self._connection = None
            logger.debug("Connection closed")

    @contextmanager
    def get_cursor(self) -> Generator[pyodbc.Cursor, None, None]:
        """Get database cursor with automatic cleanup."""
        if self._connection is None:
            self.connect()

        cursor = self._connection.cursor()
        try:
            yield cursor
        finally:
            cursor.close()

    def execute_query(self, query: str, params: tuple | None = None) -> list[dict[str, Any]]:
        """Execute query and return results as list of dicts."""
        with self.get_cursor() as cursor:
            try:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)

                columns = [column[0] for column in cursor.description]
                rows = cursor.fetchall()

                return [dict(zip(columns, row)) for row in rows]
            except pyodbc.Error as e:
                logger.error(f"Query failed: {e}")
                raise DatabaseError(f"Query failed: {e}") from e

    def execute_scalar(self, query: str, params: tuple | None = None) -> Any:
        """Execute query and return single value."""
        with self.get_cursor() as cursor:
            try:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)

                row = cursor.fetchone()
                return row[0] if row else None
            except pyodbc.Error as e:
                logger.error(f"Query failed: {e}")
                raise DatabaseError(f"Query failed: {e}") from e

    def test_connection(self) -> bool:
        """Test if database connection works."""
        try:
            self.connect()
            result = self.execute_scalar("SELECT 1")
            return result == 1
        except DatabaseError:
            return False

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
        return False
