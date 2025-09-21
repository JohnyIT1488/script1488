"""Helpers for rendering query results in a table format."""

from __future__ import annotations

from typing import Iterable, Sequence


def stringify(value: object) -> str:
    if value is None:
        return "∅"
    return str(value)


def format_table(headers: Sequence[str], rows: Iterable[Sequence[object]]) -> str:
    """Return a formatted table for CLI output."""

    rows = [tuple(stringify(value) for value in row) for row in rows]
    headers = tuple(stringify(header) for header in headers)

    if not headers:
        return "(No rows)"

    widths = [len(header) for header in headers]
    for row in rows:
        for idx, cell in enumerate(row):
            widths[idx] = max(widths[idx], len(cell))

    def format_row(row: Sequence[str]) -> str:
        cells = [cell.ljust(widths[idx]) for idx, cell in enumerate(row)]
        return " | ".join(cells)

    header_line = format_row(headers)
    separator = "-+-".join("-" * width for width in widths)
    body_lines = [format_row(row) for row in rows]

    return "\n".join([header_line, separator, *body_lines]) if body_lines else "\n".join([header_line, separator, "(No rows)"])
