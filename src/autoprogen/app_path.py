from pathlib import Path


def get_app_base_dir() -> Path:
    """Return the directory containing application resources."""
    package_dir = Path(__file__).resolve().parent
    repository_root = package_dir.parents[1]
    if (repository_root / "pyproject.toml").is_file():
        # srcレイアウトでの開発中は、リポジトリ直下のリソースを使用する。
        return repository_root

    return package_dir
