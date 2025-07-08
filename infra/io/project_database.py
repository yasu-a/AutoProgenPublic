import datetime
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator

from infra.path_providers.current_project import DatabasePathProvider
from utils.app_logging import create_logger


def adapt_datetime(val):
    assert isinstance(val, datetime.datetime), type(val)
    return val.timestamp()


sqlite3.register_adapter(datetime.datetime, adapt_datetime)


def convert_datetime(val):
    return datetime.datetime.fromtimestamp(int(val.decode("latin-1")))


sqlite3.register_converter("DATETIME", convert_datetime)


class ProjectDatabaseIO:
    _logger = create_logger()

    def __init__(
            self,
            *,
            database_path_provider: DatabasePathProvider,
    ):
        self._database_path_provider = database_path_provider

    @property
    def _database_fullpath(self) -> Path:
        return self._database_path_provider.fullpath()

    @classmethod
    def _setup_connection(cls, con: sqlite3.Connection):
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys=ON;")
        return con

    @contextmanager
    def connect(self) -> Generator[sqlite3.Connection, Any, None]:
        self._logger.debug("Connecting to database: " + str(self._database_fullpath))
        self._database_fullpath.parent.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(self._database_fullpath, detect_types=sqlite3.PARSE_DECLTYPES)
        con = self._setup_connection(con)
        self._logger.debug(f"Connection to database established ({id(con)=})")
        try:
            yield con
        except Exception as e:
            con.rollback()
            self._logger.debug(f"Connection rolled back due to exception ({id(con)=})\n{e}")
            raise
        finally:
            con.close()
            self._logger.debug(f"Connection closed ({id(con)=})")
