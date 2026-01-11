from typing import Any


def check_type(
    field_name: str,
    value: Any,
    expected_type: type,
    *,
    nullable: bool = False,
) -> None:
    if not nullable and value is None:
        raise TypeError(
            f"{field_name} must not be None"
        )
    if nullable and value is None:
        return
    if not isinstance(value, expected_type):
        raise TypeError(
            f"{field_name} must be an instance of {expected_type.__name__}, not {type(value).__name__}"
        )


def check_list(
    field_name: str,
    lst: list,
    expected_type: type,
) -> None:
    if not isinstance(lst, list):
        raise TypeError(
            f"{field_name} must be a list, not {type(lst).__name__}"
        )
    for value in lst:
        check_type(f"{field_name}[{value}]", value, expected_type)


def check_dict(
    field_name: str,
    dct: dict,
    expected_key_type: type,
    expected_value_type: type,
) -> None:
    if not isinstance(dct, dict):
        raise TypeError(
            f"{field_name} must be a dict, not {type(dct).__name__}"
        )
    for key, value in dct.items():
        check_type(f"{field_name}[{key}]", key, expected_key_type)
        check_type(f"{field_name}[{key}]", value, expected_value_type)


def check_enum(
    field_name: str,
    value: Any,
    enum_cls: type,
    *,
    nullable: bool = False,
) -> None:
    from enum import Enum

    if not issubclass(enum_cls, Enum):
        raise TypeError("enum_cls must be subclass of Enum")

    if not nullable and value is None:
        raise TypeError(f"{field_name} must not be None")
    if nullable and value is None:
        return

    if not isinstance(value, enum_cls):
        raise TypeError(
            f"{field_name} must be an instance of {enum_cls.__name__}, not {type(value).__name__}"
        )
