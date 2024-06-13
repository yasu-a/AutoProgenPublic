import codecs
import json
import os.path
import time
from datetime import datetime
from typing import NamedTuple

from app_logging import create_logger


class Settings:
    _logger = create_logger()

    def __init__(self, path):
        self.__path = path
        self.__body = None

    def __load(self):
        if os.path.exists(self.__path):
            with codecs.open(self.__path, "r", "utf-8") as f:
                self.__body = json.load(f)
        else:
            self.__body = {
                "recent_projects": [],
                "compiler": {
                    "vs_dev_cmd_bat_path": None
                },
                "misc": {
                    "max_workers": 4,  # TODO: repository
                },
            }
            self.commit()
            self._logger.info(f"new settings created")

    def __ensure_loaded(self):
        if self.__body is None:
            self.__load()

    def __getitem__(self, key):
        self.__ensure_loaded()
        return self.__body[key]

    def commit(self):
        with codecs.open(self.__path, "w", "utf-8") as f:
            json.dump(self.__body, f, indent=2, ensure_ascii=False)


class RecentProjectEntry(NamedTuple):
    fullpath: str
    updated: datetime

    @classmethod
    def from_json(cls, body):
        assert isinstance(body, dict), body
        return cls(
            fullpath=body["fullpath"],
            updated=datetime.fromtimestamp(body["updated"]),
        )

    def to_json(self):
        return dict(
            fullpath=self.fullpath,
            updated=self.updated.timestamp(),
        )


class RecentProjectRepository:
    def __init__(self, settings: Settings):
        self.__settings = settings

    def list_sorted(self) -> list[RecentProjectEntry]:
        return sorted(
            [
                RecentProjectEntry.from_json(item)
                for item in self.__settings["recent_projects"]
                if os.path.exists(item["fullpath"])
            ],
            key=lambda x: x.updated,
            reverse=True,
        )

    def find_by_path(self, project_path) -> RecentProjectEntry | None:
        for project in self.__settings["recent_projects"]:
            if project["fullpath"] == project_path:
                return project
        return None

    def add_if_absent(self, project_path):
        if self.find_by_path(project_path) is not None:
            return
        self.__settings["recent_projects"].append(
            {
                "fullpath": project_path,
                "updated": time.time(),
            }
        )
        self.__settings.commit()

    def commit(self):
        self.__settings.commit()


class CompilerRepository:
    def __init__(self, settings: Settings):
        self.__settings = settings

    def get_vs_dev_cmd_bat_path(self):
        return self.__settings["compiler"]["vs_dev_cmd_bat_path"]

    def set_vs_dev_cmd_bat_path(self, vs_dev_cmd_bat_path):
        self.__settings["compiler"]["vs_dev_cmd_bat_path"] = vs_dev_cmd_bat_path

    def commit(self):
        self.__settings.commit()


class MiscRepository:
    def __init__(self, settings: Settings):
        self.__settings = settings

    def get_max_workers(self):
        return self.__settings["misc"]["max_workers"]


_settings = Settings("./settings.json")
settings_recent_projects = RecentProjectRepository(_settings)
settings_compiler = CompilerRepository(_settings)
settings_misc = MiscRepository(_settings)
