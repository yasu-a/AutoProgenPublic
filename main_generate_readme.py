import itertools
import re
from abc import ABC, abstractmethod
from functools import cache
from pathlib import Path
from typing import Any

from application.container import AppContainer
from domain.model.app_version import ReleaseType, AppVersion
from infra.path_layout import AppPathConfig


@cache
def _get_app_path_config() -> AppPathConfig:
    return AppPathConfig.production()


@cache
def _get_app_container() -> AppContainer:
    return AppContainer(
        app_path_config=_get_app_path_config(),
    )


def _get_global_base_path() -> Path:
    return _get_app_path_config().app_base_dir


def _get_static_resource_base_path() -> Path:
    return _get_global_base_path() / "static"


def _get_icon_fullpath(filename: str) -> Path:
    return _get_static_resource_base_path() / "icon" / f"{filename}.png"


def _get_image_fullpath(filename: str) -> Path:
    return _get_static_resource_base_path() / "img" / f"{filename}.jpg"


def _get_readme_template_fullpath() -> Path:
    return _get_static_resource_base_path() / "readme" / "README.md"


class VariableFactory(ABC):
    @abstractmethod
    def __getitem__(self, var_name: str) -> Any:
        raise NotImplementedError()


class ResourceIconVariableFactory(VariableFactory):
    def __getitem__(self, var_name: str) -> Any:
        if not var_name.startswith("icon_"):
            raise KeyError(var_name)

        icon_filename = var_name[5:]
        icon_path = _get_icon_fullpath(icon_filename).relative_to(_get_global_base_path())
        return f"<img src=\"/{icon_path.as_posix()}\" width=\"15px\">"


class ResourceImageVariableFactory(VariableFactory):
    def __getitem__(self, var_name: str) -> Any:
        if not var_name.startswith("img_"):
            raise KeyError(var_name)

        image_filename = var_name[4:]
        image_path = _get_image_fullpath(image_filename).relative_to(_get_global_base_path())
        return f"![image_filename]({image_path.as_posix()})"


def _get_app_version() -> AppVersion:
    return _get_app_container().app_version_repository.get()


class AppInfoVariableFactory(VariableFactory):
    def __getitem__(self, var_name: str) -> Any:
        if var_name == "app_version":
            return str(_get_app_version())

        raise KeyError(var_name)


class AppStateVariableFactory(VariableFactory):
    def __getitem__(self, var_name: str) -> Any:
        app_version = _get_app_version()

        if var_name == "is_alpha":
            return app_version.release_type == ReleaseType.ALPHA
        if var_name == "is_beta":
            return app_version.release_type == ReleaseType.BETA
        if var_name == "is_stable":
            return app_version.is_stable

        raise KeyError(var_name)


class ChainedVariableFactory(VariableFactory):
    def __init__(self, *factories: VariableFactory):
        self._factories = factories

    def __getitem__(self, var_name: str) -> Any:
        for factory in self._factories:
            try:
                return factory[var_name]
            except KeyError:
                continue

        raise KeyError(var_name)


class TemplateParser:
    def __init__(self, variable_factory: VariableFactory):
        self._variable_factory = variable_factory

    def parse(self, text: str) -> str:
        lines: list[str | None] = text.split("\n")
        skip_lines = 0

        for i in range(len(lines)):
            # スキップの必要があればスキップ
            if skip_lines > 0:
                lines[i] = None
                skip_lines -= 1
                continue

            targets = []
            for match in re.finditer(r"\$\{(!?[\w-]+)}", lines[i]):
                targets.append(
                    dict(
                        begin=match.start(),
                        end=match.end(),
                        var_name=match.group(1),
                    )
                )

            # 置換要素のvar_nameがディレクティブ（!から始まる）なら
            targets_src = targets.copy()
            if len(targets) > 0 and targets[0]["var_name"].startswith("!"):
                directive_name = targets.pop(0)["var_name"][1:]
                # skip-lines-unless 例: ${!skip-lines-unless} ${is_alpha} ${3} is_alphaなら3行スキップ
                if directive_name == "skip-lines-unless":
                    condition = bool(self._variable_factory[targets.pop(0)["var_name"]])
                    n_skip_lines = int(targets.pop(0)["var_name"])
                    if not condition:
                        skip_lines = n_skip_lines
                else:
                    assert False, ("unknown directive", targets)

            # 普通に置換
            for target in reversed(targets_src):
                left_substr = lines[i][:target["begin"]]

                if target in targets:
                    replacement = self._variable_factory[target["var_name"]]
                else:
                    replacement = ""

                right_substr = lines[i][target["end"]:]
                lines[i] = f"{left_substr}{replacement!s}{right_substr}"

        header = [
            "<!-- このファイルは main_generate_readme.py で自動生成されています -->",
            "<!-- 編集する場合はテンプレート static/readme/README.md を編集して再生成します --> ",
        ]

        return "\n".join(
            itertools.chain(
                header,
                [""],
                (line for line in lines if line is not None),
            )
        )


def main() -> None:
    readme_text = TemplateParser(
        variable_factory=ChainedVariableFactory(
            ResourceIconVariableFactory(),
            ResourceImageVariableFactory(),
            AppInfoVariableFactory(),
            AppStateVariableFactory(),
        )
    ).parse(
        _get_readme_template_fullpath().read_text(encoding="utf-8")
    )

    Path("README.md").write_text(
        readme_text,
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()