from typing import Dict, NamedTuple

from dataclassy import as_dict, dataclass, fields
from eth_abi import is_encodable_type
from eth_typing import Hash32
from eth_utils.curried import ValidationError, keccak
from hexbytes import HexBytes

# isort: off
# We need isort off for these two imports because black makes a conflicting change.
from .hashing import hash_domain  # type:ignore
from .hashing import hash_message as hash_eip712_message

EIP712_DOMAIN_FIELDS = [
    "name",
    "version",
    "chainId",
    "verifyingContract",
]
HEADER_FIELDS = set(f"_{field}_" for field in EIP712_DOMAIN_FIELDS)


# https://github.com/ethereum/eth-account/blob/f1d38e0/eth_account/messages.py#L39
class SignableMessage(NamedTuple):
    """
    These are the components of an EIP-191_ signable message. Other message formats
    can be encoded into this format for easy signing. This data structure doesn't need to
    know about the original message format.

    In typical usage, you should never need to create these by hand. Instead, use
    one of the available encode_* methods in this module, like:

        - :meth:`encode_structured_data`
        - :meth:`encode_intended_validator`
        - :meth:`encode_structured_data`

    .. _EIP-191: https://eips.ethereum.org/EIPS/eip-191
    """

    version: bytes  # must be length 1
    header: bytes  # aka "version specific data"
    body: bytes  # aka "data to sign"


# https://github.com/ethereum/eth-account/blob/f1d38e0/eth_account/messages.py#L59
def _hash_eip191_message(signable_message: SignableMessage) -> Hash32:
    version = signable_message.version
    if len(version) != 1:
        raise ValidationError(
            "The supplied message version is {version!r}. "
            "The EIP-191 signable message standard only supports one-byte versions."
        )

    joined = b"\x19" + version + signable_message.header + signable_message.body
    return Hash32(keccak(joined))


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
        d = as_dict(self)  # NOTE: Handles recursion
        return {k: v for (k, v) in d.items() if k not in HEADER_FIELDS}


# TODO: Make type of EIP712Message a subtype of SignableMessage somehow
class EIP712Message(EIP712Type):
    def __post_init__(self):
        # At least one of the header fields must be in the EIP712 message header
        if len(self.domain) == 0:
            raise ValidationError(
                f"EIP712 Message definition '{self.type}' must define "
                f"at least one of {EIP712_DOMAIN_FIELDS}"
            )

    @property
    def domain(self) -> dict:
        return {
            field.replace("_", ""): getattr(self, field)
            for field in fields(self.__class__, internals=True)
            if field in HEADER_FIELDS
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
    def body_data(self) -> dict:
        types = dict(self.types(), EIP712Domain=self.domain_type)
        msg = {
            "domain": self.domain,
            "types": types,
            "primaryType": self.type,
            "message": self.data,
        }
        return msg

    @property
    def body(self) -> bytes:
        return hash_eip712_message(self.body_data)

    @property
    def signable_message(self) -> SignableMessage:
        return SignableMessage(
            HexBytes(b"\x01"),
            self.header,
            self.body,
        )
