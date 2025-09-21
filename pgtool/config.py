"""Configuration helpers for pgtool."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, Optional
import os

try:  # Python >= 3.11
    import tomllib  # type: ignore[attr-defined]
except ModuleNotFoundError:  # pragma: no cover - fallback for <3.11
    import tomli as tomllib  # type: ignore[no-redef]


@dataclass(slots=True)
class DatabaseConfig:
    """Parameters required to establish a PostgreSQL connection."""

    host: Optional[str] = None
    port: Optional[int] = None
    user: Optional[str] = None
    password: Optional[str] = None
    database: Optional[str] = None
    dsn: Optional[str] = None
    options: Dict[str, str] = field(default_factory=dict)

    def merged_with(self, other: "DatabaseConfig") -> "DatabaseConfig":
        """Return a new config where ``other`` overrides ``self``."""

        return DatabaseConfig(
            host=other.host or self.host,
            port=other.port or self.port,
            user=other.user or self.user,
            password=other.password or self.password,
            database=other.database or self.database,
            dsn=other.dsn or self.dsn,
            options={**self.options, **other.options},
        )

    def to_connect_kwargs(self) -> Dict[str, object]:
        """Translate the configuration into ``psycopg2.connect`` kwargs."""

        if self.dsn:
            return {"dsn": self.dsn}

        kwargs: Dict[str, object] = {k: v for k, v in (
            ("host", self.host),
            ("port", self.port),
            ("user", self.user),
            ("password", self.password),
            ("dbname", self.database),
        ) if v is not None}
        kwargs.update(self.options)
        return kwargs

    @classmethod
    def from_mapping(cls, mapping: Dict[str, object]) -> "DatabaseConfig":
        """Create a configuration instance from a raw mapping."""

        options = mapping.get("options")
        if not isinstance(options, dict):
            options = {}

        port = mapping.get("port")
        if isinstance(port, str) and port.isdigit():
            port = int(port)
        elif isinstance(port, (float, int)):
            port = int(port)
        else:
            port = None if port is None else int(port)

        return cls(
            host=mapping.get("host") or None,
            port=port,
            user=mapping.get("user") or None,
            password=mapping.get("password") or None,
            database=mapping.get("database") or None,
            dsn=mapping.get("dsn") or None,
            options={str(k): str(v) for k, v in options.items()},
        )

    @classmethod
    def from_environment(cls, prefix: str = "PGTOOL_") -> "DatabaseConfig":
        """Load configuration from environment variables."""

        data: Dict[str, object] = {}
        options: Dict[str, str] = {}
        for key, value in os.environ.items():
            if not key.startswith(prefix):
                continue
            raw_key = key[len(prefix):]
            if raw_key.startswith("OPTION_"):
                option_key = raw_key[len("OPTION_"):].lower()
                options[option_key] = value
            else:
                data[raw_key.lower()] = value
        if options:
            data["options"] = options
        return cls.from_mapping(data)


DEFAULT_CONFIG_LOCATIONS = (
    Path.cwd() / "pgtool.toml",
    Path.home() / ".pgtool.toml",
    Path.home() / ".config" / "pgtool" / "config.toml",
)


def load_config(path: Optional[str] = None) -> DatabaseConfig:
    """Load configuration from a TOML file if it exists."""

    candidate_paths: Iterable[Path]
    if path:
        candidate_paths = (Path(path),)
    else:
        candidate_paths = DEFAULT_CONFIG_LOCATIONS

    for candidate in candidate_paths:
        if candidate.is_file():
            with candidate.open("rb") as fh:
                data = tomllib.load(fh)
            db_section = data.get("database") if isinstance(data, dict) else None
            if not isinstance(db_section, dict):
                raise ValueError(f"Configuration file {candidate} missing [database] section")
            return DatabaseConfig.from_mapping(db_section)

    return DatabaseConfig()


def merge_configs(configs: Iterable[DatabaseConfig]) -> DatabaseConfig:
    """Merge a collection of configurations, later ones winning."""

    merged = DatabaseConfig()
    for config in configs:
        merged = merged.merged_with(config)
    return merged
