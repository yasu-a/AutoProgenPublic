from pathlib import Path


def get_app_base_dir() -> Path:
    """Return the directory containing application resources."""
    package_dir = Path(__file__).resolve().parent
    if (package_dir / "app_version.json").is_file():
        return package_dir

    # During the src-layout migration, resources remain in the repository root.
    return package_dir.parents[1]
