"""Command line helpers for convenient work with PostgreSQL."""
from __future__ import annotations

import argparse
import csv
import getpass
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence

try:  # pragma: no cover - the dependency check is trivial
    import psycopg
    from psycopg import sql
    from psycopg.rows import dict_row
except ImportError as exc:  # pragma: no cover - handled at runtime
    raise SystemExit(
        "The 'psycopg' package is required for pg_tool. Install it with "
        "'pip install psycopg'."
    ) from exc


@dataclass
class ConnectionConfig:
    """Configuration parameters for a PostgreSQL connection."""

    dsn: Optional[str] = None
    host: Optional[str] = None
    port: int = 5432
    dbname: Optional[str] = None
    user: Optional[str] = None
    password: Optional[str] = None
    autocommit: bool = False

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> "ConnectionConfig":
        password = args.password
        if password is None and args.ask_password:
            password = getpass.getpass("Password: ")
        return cls(
            dsn=args.dsn,
            host=args.host,
            port=args.port,
            dbname=args.dbname,
            user=args.user,
            password=password,
            autocommit=args.autocommit,
        )

    def to_connection_kwargs(self) -> dict:
        if self.dsn:
            return {"conninfo": self.dsn}
        kwargs = {}
        if self.host:
            kwargs["host"] = self.host
        if self.port:
            kwargs["port"] = self.port
        if self.dbname:
            kwargs["dbname"] = self.dbname
        if self.user:
            kwargs["user"] = self.user
        if self.password:
            kwargs["password"] = self.password
        return kwargs


def _parse_table_name(table: str) -> tuple[str, str]:
    if "." in table:
        schema, name = table.split(".", 1)
        return schema, name
    return "public", table


class DatabaseClient:
    """Small wrapper above psycopg connections providing helper utilities."""

    def __init__(self, config: ConnectionConfig):
        kwargs = config.to_connection_kwargs()
        self.connection = psycopg.connect(**kwargs)
        self.connection.autocommit = config.autocommit

    def __enter__(self) -> "DatabaseClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def close(self) -> None:
        self.connection.close()

    def execute(self, statement: sql.Composable | str, *params) -> psycopg.Cursor:
        cur = self.connection.cursor(row_factory=dict_row)
        cur.execute(statement, params if params else None)
        return cur

    def list_tables(self, schema: Optional[str] = None) -> Sequence[str]:
        schema_clause = " AND table_schema = %s" if schema else ""
        query = (
            "SELECT table_schema || '.' || table_name AS name "
            "FROM information_schema.tables "
            "WHERE table_type = 'BASE TABLE'" + schema_clause +
            " ORDER BY table_schema, table_name"
        )
        params: Sequence[str] = (schema,) if schema else ()
        with self.execute(query, *params) as cursor:
            return [row["name"] for row in cursor.fetchall()]

    def describe_table(self, table: str) -> Sequence[dict]:
        schema, name = _parse_table_name(table)
        query = (
            "SELECT column_name, data_type, is_nullable, column_default "
            "FROM information_schema.columns "
            "WHERE table_schema = %s AND table_name = %s "
            "ORDER BY ordinal_position"
        )
        with self.execute(query, schema, name) as cursor:
            return cursor.fetchall()

    def run_query(self, query: str) -> tuple[Sequence[str], Sequence[Sequence[object]]]:
        with self.execute(query) as cursor:
            if cursor.description is None:
                self.connection.commit()
                return (), ()
            rows = cursor.fetchall()
            headers = [desc.name for desc in cursor.description]
            return headers, [[row[col] for col in headers] for row in rows]

    def export_table(self, table: str, path: Path) -> None:
        schema, name = _parse_table_name(table)
        query = sql.SQL("SELECT * FROM {}.{}").format(
            sql.Identifier(schema), sql.Identifier(name)
        )
        with self.execute(query) as cursor:
            headers = [desc.name for desc in cursor.description or ()]
            rows = cursor.fetchall()
        if not headers:
            return
        with path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(headers)
            writer.writerows(rows)

    def import_csv(self, table: str, path: Path, *, truncate: bool = False) -> int:
        schema, name = _parse_table_name(table)
        with path.open("r", newline="", encoding="utf-8") as file:
            reader = csv.reader(file)
            headers = next(reader)
            values = list(reader)
        if truncate:
            truncate_stmt = sql.SQL("TRUNCATE TABLE {}.{}").format(
                sql.Identifier(schema), sql.Identifier(name)
            )
            with self.connection.cursor() as cursor:
                cursor.execute(truncate_stmt)
        placeholders = sql.SQL(", ").join(sql.Placeholder() for _ in headers)
        columns = sql.SQL(", ").join(sql.Identifier(col) for col in headers)
        insert_stmt = sql.SQL("INSERT INTO {}.{} ({}) VALUES ({})").format(
            sql.Identifier(schema),
            sql.Identifier(name),
            columns,
            placeholders,
        )
        with self.connection.cursor() as cursor:
            cursor.executemany(insert_stmt, values)
        self.connection.commit()
        return len(values)


def format_table(headers: Sequence[str], rows: Sequence[Sequence[object]]) -> str:
    if not headers:
        return "(empty result)"
    str_rows = [["" if value is None else str(value) for value in row] for row in rows]
    widths = [len(header) for header in headers]
    for row in str_rows:
        for index, value in enumerate(row):
            widths[index] = max(widths[index], len(value))

    def fmt_row(row: Sequence[str]) -> str:
        return " | ".join(value.ljust(widths[index]) for index, value in enumerate(row))

    line = "-+-".join("-" * width for width in widths)
    output = [fmt_row(headers), line]
    output.extend(fmt_row(row) for row in str_rows)
    return "\n".join(output)


class InteractiveShell:
    """Simple interactive shell for executing commands against PostgreSQL."""

    prompt = "pg> "

    def __init__(self, client: DatabaseClient):
        self.client = client

    def cmdloop(self) -> None:
        print("Type 'help' for a list of commands. Type 'quit' to exit.")
        while True:
            try:
                command = input(self.prompt).strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not command:
                continue
            if command in {"quit", "exit"}:
                break
            if command == "help":
                self.print_help()
                continue
            self.handle_command(command)

    def print_help(self) -> None:
        print(
            "Available commands:\n"
            "  tables [schema]   - list tables in the database\n"
            "  describe <table>  - show table columns\n"
            "  query <sql>       - execute an arbitrary SQL query\n"
            "  export <table> <path> - export table to CSV\n"
            "  import <table> <path> [--truncate] - import CSV into a table\n"
            "  help              - show this message\n"
            "  quit/exit         - leave the shell"
        )

    def handle_command(self, command: str) -> None:
        parts = command.split()
        if not parts:
            return
        cmd, *args = parts
        try:
            if cmd == "tables":
                schema = args[0] if args else None
                tables = self.client.list_tables(schema)
                print("\n".join(tables) if tables else "(no tables found)")
            elif cmd == "describe":
                if not args:
                    print("Usage: describe <schema.table>")
                    return
                columns = self.client.describe_table(args[0])
                if not columns:
                    print("Table not found or has no columns.")
                    return
                headers = ["column_name", "data_type", "is_nullable", "column_default"]
                rows = [[col[h] for h in headers] for col in columns]
                print(format_table(headers, rows))
            elif cmd == "query":
                if not args:
                    print("Usage: query <sql>")
                    return
                sql = " ".join(args)
                headers, rows = self.client.run_query(sql)
                print(format_table(headers, rows))
            elif cmd == "export":
                if len(args) != 2:
                    print("Usage: export <schema.table> <path>")
                    return
                table, path_str = args
                path = Path(path_str).expanduser()
                self.client.export_table(table, path)
                print(f"Exported {table} to {path}")
            elif cmd == "import":
                if len(args) < 2:
                    print("Usage: import <schema.table> <path> [--truncate]")
                    return
                table = args[0]
                path = Path(args[1]).expanduser()
                truncate = "--truncate" in args[2:]
                count = self.client.import_csv(table, path, truncate=truncate)
                print(f"Imported {count} rows into {table}")
            else:
                print(f"Unknown command: {cmd}. Type 'help' for instructions.")
        except psycopg.Error as exc:
            print(f"Error: {exc}")


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dsn", help="Connection string (overrides other parameters)")
    parser.add_argument("--host", default=os.getenv("PGHOST", "localhost"))
    parser.add_argument("--port", type=int, default=int(os.getenv("PGPORT", 5432)))
    parser.add_argument("--dbname", default=os.getenv("PGDATABASE", "postgres"))
    parser.add_argument("--user", default=os.getenv("PGUSER"))
    parser.add_argument("--password", default=os.getenv("PGPASSWORD"))
    parser.add_argument("--ask-password", action="store_true", help="Prompt for password")
    parser.add_argument(
        "--autocommit",
        action="store_true",
        help="Enable autocommit mode for the connection",
    )

    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("shell", help="Open an interactive shell")

    tables_parser = subparsers.add_parser("tables", help="List tables")
    tables_parser.add_argument("schema", nargs="?", help="Optional schema name")

    describe_parser = subparsers.add_parser("describe", help="Describe a table")
    describe_parser.add_argument("table", help="Table name in schema.table format")

    query_parser = subparsers.add_parser("query", help="Execute arbitrary SQL")
    query_parser.add_argument("sql", help="SQL to execute")

    export_parser = subparsers.add_parser("export", help="Export table to CSV")
    export_parser.add_argument("table", help="Table name in schema.table format")
    export_parser.add_argument("path", help="Destination CSV file")

    import_parser = subparsers.add_parser("import", help="Import CSV data")
    import_parser.add_argument("table", help="Table name in schema.table format")
    import_parser.add_argument("path", help="Path to CSV file")
    import_parser.add_argument(
        "--truncate",
        action="store_true",
        help="Truncate the table before importing",
    )

    return parser.parse_args(argv)


def run_cli(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    config = ConnectionConfig.from_args(args)
    try:
        with DatabaseClient(config) as client:
            if args.command == "shell" or args.command is None:
                InteractiveShell(client).cmdloop()
                return 0
            if args.command == "tables":
                tables = client.list_tables(args.schema)
                print("\n".join(tables) if tables else "(no tables found)")
            elif args.command == "describe":
                columns = client.describe_table(args.table)
                if not columns:
                    print("Table not found or has no columns.")
                    return 1
                headers = ["column_name", "data_type", "is_nullable", "column_default"]
                rows = [[col[h] for h in headers] for col in columns]
                print(format_table(headers, rows))
            elif args.command == "query":
                headers, rows = client.run_query(args.sql)
                print(format_table(headers, rows))
            elif args.command == "export":
                path = Path(args.path).expanduser()
                client.export_table(args.table, path)
                print(f"Exported {args.table} to {path}")
            elif args.command == "import":
                path = Path(args.path).expanduser()
                count = client.import_csv(args.table, path, truncate=args.truncate)
                print(f"Imported {count} rows into {args.table}")
        return 0
    except psycopg.Error as exc:
        print(f"Database error: {exc}", file=sys.stderr)
        return 2


def main() -> None:
    sys.exit(run_cli())


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
