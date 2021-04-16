from typing import Dict

from dataclassy import as_dict, dataclass, fields
from eth_abi import is_encodable_type
from eth_utils.curried import ValidationError

# isort: off
# We need isort off for these two imports because black makes a conflicting change.
from .hashing import hash_domain  # type:ignore
from .hashing import (
    hash_message as hash_eip712_message,
)

EIP712_DOMAIN_FIELDS = [
    "name",
    "version",
    "chainId",
    "verifyingContract",
]


@dataclass(iter=True, slots=True)
class EIP712Type:
    @property
    def type(self) -> str:
        return self.__class__.__name__

    def field_type(self, field: str) -> str:
        typ = self.__annotations__[field]

        if isinstance(typ, str):
            if not is_encodable_type(typ):
                raise ValidationError(f"'{field}: {typ}' is not a valid ABI type")

            return typ

        elif issubclass(typ, EIP712Type):
            return typ.type

        else:
            raise ValidationError(
                f"'{field}' type annotation must either be a subclass of "
                f"`EIP712Type` or valid ABI Type string, not {typ.__class__.__name__}"
            )

    def types(self) -> dict:
        types: Dict[str, list] = {}
        types[self.type] = []

        for field in fields(self.__class__):
            value = getattr(self, field)
            if isinstance(value, EIP712Type):
                types[self.type].append({"name": field, "type": value.type})
                types.update(value.types())
            else:
                types[self.type].append({"name": field, "type": self.field_type(field)})

        return types

    @property
    def data(self) -> dict:
        return as_dict(self)  # NOTE: Handles recursion


# TODO: Make type of EIP712Message a subtype of SignableMessage somehow
class EIP712Message(EIP712Type):
    def __init__(self):
        # At least one of the header fields must be in the EIP712 message header
        if len(self.domain) == 0:
            raise ValidationError(
                f"EIP712 Message definition '{self.type}' must define "
                f"at least one of {EIP712_DOMAIN_FIELDS}"
            )

    @property
    def domain(self) -> dict:
        header_fields = [f"_{field}_" for field in EIP712_DOMAIN_FIELDS]
        return {
            field.replace("_", ""): getattr(self, field)
            for field in fields(self.__class__, internals=True)
            if field in header_fields
        }

    @property
    def domain_type(self) -> list:
        return [{"name": field, "type": self.field_type(f"_{field}_")} for field in self.domain]

    @property
    def version(self) -> bytes:
        return b"\x01"

    @property
    def header(self) -> bytes:
        return hash_domain(
            {
                "types": {
                    "EIP712Domain": self.domain_type,
                },
                "domain": self.domain,
            }
        )

    @property
    def body(self) -> bytes:
        msg = {
            "types": self.types(),
            "primaryType": self.type,
            "message": self.data,
        }
        return hash_eip712_message(msg)
