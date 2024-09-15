# from hashlib import md5
# 
# M = 2 ** 64
# 
# 
# 
# def permanent_hash(obj) -> int:
#     if isinstance(obj, bytes):
#         return int.from_bytes(md5(obj).digest(), byteorder="big")
#     elif isinstance(obj, str):
#         return permanent_hash(obj.encode("utf-8"))
#     elif isinstance(obj, (int, float)):
#         return permanent_hash(f"{type(obj)} {obj!r}")
#     elif isinstance(obj, (list, tuple)):
#         h = 0
#         for item in obj:
#             h = (h * 31 + permanent_hash(item)) % M
#         return h
#     elif isinstance(obj, dict):
#         return permanent_hash()
