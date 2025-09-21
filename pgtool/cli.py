"""Command line interface for pgtool."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable, List, Sequence
import ast

from .config import DatabaseConfig, load_config, merge_configs
from .db import DatabaseConnection
from .render import format_table


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Утилита для удобной работы с PostgreSQL",
    )

    parser.add_argument("--config", help="Путь до TOML файла конфигурации", default=None)
    parser.add_argument("--dsn", help="Строка подключения" , default=None)
    parser.add_argument("--host", help="Хост PostgreSQL", default=None)
    parser.add_argument("--port", type=int, help="Порт PostgreSQL", default=None)
    parser.add_argument("--user", help="Пользователь", default=None)
    parser.add_argument("--password", help="Пароль", default=None)
    parser.add_argument("--database", help="База данных", default=None)
    parser.add_argument(
        "--option",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Дополнительные параметры подключения",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    query_parser = subparsers.add_parser("query", help="Выполнить SQL запрос")
    query_parser.add_argument("sql", nargs="?", help="SQL выражение для выполнения")
    query_parser.add_argument("--file", "-f", help="Путь до SQL файла")
    query_parser.add_argument(
        "--no-fetch",
        action="store_true",
        help="Не возвращать результаты (для INSERT/UPDATE/DELETE)",
    )
    query_parser.add_argument(
        "--params",
        nargs="*",
        default=[],
        metavar="VALUE",
        help="Параметры запроса (позиционные)",
    )

    tables_parser = subparsers.add_parser("tables", help="Показать список таблиц")
    tables_parser.add_argument(
        "--include-system",
        action="store_true",
        help="Отображать системные схемы",
    )

    describe_parser = subparsers.add_parser("describe", help="Описание таблицы")
    describe_parser.add_argument("table", help="Имя таблицы, можно schema.table")

    export_parser = subparsers.add_parser("export", help="Выгрузить результат запроса в CSV")
    export_parser.add_argument("--output", "-o", required=True, help="Путь до CSV файла")
    export_parser.add_argument("sql", nargs="?", help="SQL выражение")
    export_parser.add_argument("--file", "-f", help="Путь до SQL файла")
    export_parser.add_argument(
        "--params",
        nargs="*",
        default=[],
        metavar="VALUE",
        help="Параметры запроса (позиционные)",
    )

    script_parser = subparsers.add_parser("script", help="Выполнить SQL скрипт")
    script_parser.add_argument("path", help="Файл SQL со множеством выражений")

    return parser


def parse_options(options: Iterable[str]) -> dict:
    parsed = {}
    for option in options:
        if "=" not in option:
            raise ValueError(f"Параметр опции должен быть в формате KEY=VALUE, получено: {option}")
        key, value = option.split("=", 1)
        parsed[key.strip()] = value.strip()
    return parsed


def parse_params(params: Sequence[str]) -> List[object]:
    parsed: List[object] = []
    for param in params:
        try:
            parsed.append(ast.literal_eval(param))
        except (ValueError, SyntaxError):
            parsed.append(param)
    return parsed


def read_sql(sql: str | None, file_path: str | None) -> str:
    if sql and file_path:
        raise ValueError("Нельзя одновременно передать SQL и путь до файла")
    if sql:
        return sql
    if file_path:
        return Path(file_path).read_text(encoding="utf-8")
    raise ValueError("Нужно передать SQL выражение либо путь до файла")


def build_config(args: argparse.Namespace) -> DatabaseConfig:
    file_config = load_config(args.config)
    env_config = DatabaseConfig.from_environment()

    mapping = {key: getattr(args, key) for key in ("host", "port", "user", "password", "database", "dsn")}
    option_mapping = parse_options(args.option)
    mapping["options"] = option_mapping
    cli_config = DatabaseConfig.from_mapping(mapping)

    return merge_configs((file_config, env_config, cli_config))


def handle_query(db: DatabaseConnection, args: argparse.Namespace) -> None:
    sql = read_sql(args.sql, args.file)
    params = parse_params(args.params)
    columns, rows = db.run_query(sql, params=params, fetch=not args.no_fetch)
    if args.no_fetch:
        print("Запрос выполнен успешно, результаты не возвращены")
    else:
        if not rows:
            print("(Нет строк)")
        else:
            print(format_table(columns, rows))


def handle_tables(db: DatabaseConnection, args: argparse.Namespace) -> None:
    rows = db.list_tables(include_system=args.include_system)
    headers = ("schema", "table")
    if not rows:
        print("(Нет таблиц)")
    else:
        print(format_table(headers, rows))


def handle_describe(db: DatabaseConnection, args: argparse.Namespace) -> None:
    rows = db.describe_table(args.table)
    headers = ("column", "type", "nullable", "default")
    if not rows:
        print("Таблица не найдена или не содержит колонок")
    else:
        print(format_table(headers, rows))


def handle_export(db: DatabaseConnection, args: argparse.Namespace) -> None:
    sql = read_sql(args.sql, args.file)
    params = parse_params(args.params)
    destination = Path(args.output)
    db.export_to_csv(sql, destination, params=params)
    print(f"Результат сохранён в {destination}")


def handle_script(db: DatabaseConnection, args: argparse.Namespace) -> None:
    sql = Path(args.path).read_text(encoding="utf-8")
    db.execute_script(sql)
    print("Скрипт выполнен успешно")


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        config = build_config(args)
        with DatabaseConnection(config) as db:
            if args.command == "query":
                handle_query(db, args)
            elif args.command == "tables":
                handle_tables(db, args)
            elif args.command == "describe":
                handle_describe(db, args)
            elif args.command == "export":
                handle_export(db, args)
            elif args.command == "script":
                handle_script(db, args)
            else:  # pragma: no cover - argparse ensures we don't reach here
                parser.error(f"Неизвестная команда: {args.command}")
    except Exception as exc:  # broad for CLI messaging
        print(f"Ошибка: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
