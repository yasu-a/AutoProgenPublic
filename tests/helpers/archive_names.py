def normalize_archive_name(name: str) -> str:
    normalized = name.strip()
    if not normalized:
        raise AssertionError("archive name must not be empty")
    if not normalized.endswith(".zip"):
        normalized = normalized + ".zip"
    return normalized
