from dataclasses import dataclass
from typing import TypeVar, Generic

K = TypeVar("K")  # key type
V = TypeVar("V")  # value type


@dataclass(slots=True)
class LRUCacheEntry(Generic[V]):
    v: V
    age: int


class LRUCache(Generic[K, V]):
    def __init__(self, max_size: int, reduced_size: int):
        assert 0 < reduced_size < max_size

        self.__max_size = max_size
        self.__reduced_size = reduced_size

        self.__cache: dict[K, LRUCacheEntry[V]] = {}
        self.__next_age = 0

    def __get_next_age(self) -> int:
        self.__next_age += 1
        return self.__next_age

    def __reduce_if_needed(self):
        if len(self.__cache) < self.__max_size:
            return

        entries = list(self.__cache.items())
        entries.sort(key=lambda item: item[1].age, reverse=True)

        self.__cache.clear()
        for i in range(self.__reduced_size):
            k, entry = entries[i]
            self.__cache[k] = entry

    def __contains__(self, k: K) -> bool:
        return k in self.__cache

    def __getitem__(self, k: K) -> V:
        return self.__cache[k].v

    def __setitem__(self, k: K, v: V) -> None:
        # noinspection PyArgumentList
        self.__cache[k] = LRUCacheEntry[V](v=v, age=self.__next_age)
        self.__reduce_if_needed()

    def __delitem__(self, k: K) -> None:
        del self.__cache[k]
