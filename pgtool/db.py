"""Database utilities wrapping psycopg2."""

from __future__ import annotations

import csv
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable, Iterator, Optional, Sequence, Tuple

import psycopg2

from .config import DatabaseConfig

Row = Tuple[object, ...]


class DatabaseConnection:
    """A lightweight helper around a PostgreSQL connection."""

    def __init__(self, config: DatabaseConfig) -> None:
        self._config = config
        self._connection: Optional[psycopg2.extensions.connection] = None

    def connect(self) -> psycopg2.extensions.connection:
        if self._connection is None:
            kwargs = self._config.to_connect_kwargs()
            self._connection = psycopg2.connect(**kwargs)
        return self._connection

    def close(self) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def __enter__(self) -> "DatabaseConnection":  # pragma: no cover - convenience wrapper
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - convenience wrapper
        self.close()

    @contextmanager
    def cursor(self) -> Iterator[psycopg2.extensions.cursor]:
        connection = self.connect()
        cursor = connection.cursor()
        try:
            yield cursor
        finally:
            cursor.close()

    def run_query(self, query: str, params: Optional[Sequence[object]] = None, fetch: bool = True) -> Tuple[Sequence[str], Sequence[Row]]:
        """Execute a query and optionally fetch results."""

        with self.cursor() as cursor:
            cursor.execute(query, params)
            if fetch and cursor.description:
                columns = [col.name if hasattr(col, "name") else col[0] for col in cursor.description]
                rows = cursor.fetchall()
            else:
                columns, rows = (), ()
            if not fetch:
                self.connect().commit()
        return columns, rows

    def list_tables(self, include_system: bool = False) -> Sequence[Row]:
        """Return schema and table name for available tables."""

        if include_system:
            schema_filter = ""
        else:
            schema_filter = "AND table_schema NOT IN ('pg_catalog', 'information_schema')"

        query = f"""
        SELECT table_schema, table_name
        FROM information_schema.tables
        WHERE table_type = 'BASE TABLE'
        {schema_filter}
        ORDER BY table_schema, table_name
        """
        _, rows = self.run_query(query)
        return rows

    def describe_table(self, table: str) -> Sequence[Row]:
        """Return column metadata for the provided table."""

        query = """
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_schema = split_part(%s, '.', 1)
          AND table_name = split_part(%s, '.', 2)
        ORDER BY ordinal_position
        """
        schema_table = table if "." in table else f"public.{table}"
        _, rows = self.run_query(query, (schema_table, schema_table))
        return rows

    def export_to_csv(self, query: str, destination: Path, params: Optional[Sequence[object]] = None) -> Path:
        """Execute a query and store results in ``destination`` as CSV."""

        columns, rows = self.run_query(query, params=params, fetch=True)
        if not columns:
            raise ValueError("Query did not return any data to export")

        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("w", encoding="utf-8", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(columns)
            writer.writerows(rows)
        return destination

    def execute_script(self, sql: str) -> None:
        """Execute a script with potentially multiple statements."""

        with self.cursor() as cursor:
            cursor.execute(sql)
        self.connect().commit()

    def iter_query(self, query: str, params: Optional[Sequence[object]] = None, chunk_size: int = 1000) -> Iterable[Row]:
        """Iterate lazily over query results in batches."""

        with self.cursor() as cursor:
            cursor.execute(query, params)
            while True:
                chunk = cursor.fetchmany(chunk_size)
                if not chunk:
                    break
                for row in chunk:
                    yield row
