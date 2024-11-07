from pathlib import Path


def is_compiler_location(path: Path) -> bool:
    return path.is_file() and path.name == "VsDevCmd.bat"
