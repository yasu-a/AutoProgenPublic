from infra.cache.lru import LRUCache


def get_lru_cache():
    return LRUCache(max_size=1 << 12, reduced_size=1 << 11)
