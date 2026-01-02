_debug = False


# TODO: 廃止！

def set_debug(debug: bool):
    global _debug
    _debug = debug


def is_debug() -> bool:
    return _debug
