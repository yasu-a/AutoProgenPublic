from contextlib import contextmanager
import sqlite3
from pathlib import Path
from sqlite3 import Connection
from typing import Any, Generator

from infra.path_providers.current_project import DatabasePathProvider
from utils.app_logging import create_logger


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
    def _setup_connection(cls, con: Connection):
        con.row_factory = sqlite3.Row
        return con

    @contextmanager
    def connect(self) -> Generator[Connection, Any, None]:
        self._logger.debug("Connecting to database: " + str(self._database_fullpath))
        self._database_fullpath.parent.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(self._database_fullpath)
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
