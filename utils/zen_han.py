from functools import lru_cache

import unicodedata


@lru_cache(maxsize=1 << 20)
def _zen_to_han_char(ch: str):
    ch_converted = unicodedata.normalize("NFKC", ch)
    if len(ch_converted) != len(ch):
        return ch
    else:
        return ch_converted


def zen_to_han(text: str):
    # 全角を半角にノーマライズする
    return "".join(_zen_to_han_char(ch) for ch in text)
