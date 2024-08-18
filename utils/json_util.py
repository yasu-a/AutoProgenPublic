# TODO: モデルにjson化の処理を書かずに分離し、分離先に統合する

from base64 import b64encode, b64decode


def bytes_to_jsonable(s: bytes) -> str:
    return b64encode(s).decode("ascii")


def jsonable_to_bytes(s: str) -> bytes:
    return b64decode(s.encode("ascii"))
