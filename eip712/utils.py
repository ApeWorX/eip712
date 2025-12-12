from typing import TYPE_CHECKING, Any, get_args, get_origin

from eth_pydantic_types import Address, HexBytes, abi
from pydantic import BaseModel

if TYPE_CHECKING:
    # NOTE: Added to `typing` in 3.12
    from typing_extensions import TypeAliasType


# NOTE: We support these type more "native" annotations
SUPPORTED_NONABI_TYPES = {
    Address: "address",
    HexBytes: "bytes",
    bytes: "bytes",
    str: "string",
}


def is_model_type(t: Any) -> bool:
    try:
        return issubclass(t, BaseModel)

    except TypeError:
        return False


def get_abi_type(
    t: "type | TypeAliasType | tuple[type | TypeAliasType, Any, Any]",
) -> str:
    if isinstance(t, tuple):
        return get_abi_type(t[0])

    elif abi_type := SUPPORTED_NONABI_TYPES.get(t):
        return abi_type

    elif get_origin(t) is list:
        inner_type = get_abi_type(get_args(t)[0])
        return f"{inner_type}[]"

    elif t.__module__ == abi.__name__:
        return t.__name__

    elif is_model_type(t):
        return t.__name__

    raise TypeError(f"Cannot convert type {t} to abi type.")


def build_eip712_type(cls: type[BaseModel]) -> dict:
    """
    Recursively build ``dict`` (name of type ``->`` list of subtypes)
    of all underlying fields in ``cls``, according to EIP712 structural typing.
    """
    field_types: dict[str, list] = {cls.__name__: []}

    for field, field_info in cls.model_fields.items():
        if (field_type := field_info.annotation) is None:
            raise TypeError(f"Cannot process '{field}': type is None")

        elif is_model_type(field_type):  # Type is `BaseModel`
            field_types.update(build_eip712_type(field_type))

        elif (
            (get_origin(field_type := field_info.annotation) is list)
            # Inner type of `list` is `BaseModel`
            and is_model_type(inner_type := get_args(field_type)[0])
        ):
            field_types.update(build_eip712_type(inner_type))

        assert field_type is not None  # mypy issue
        field_types[cls.__name__].append({"name": field, "type": get_abi_type(field_type)})

    return field_types
