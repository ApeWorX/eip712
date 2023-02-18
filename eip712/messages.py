"""
Message classes for typed structured data hashing and signing in Ethereum.
"""

from typing import Any, Dict, Optional

from dataclassy import dataclass, fields
from eth_abi import is_encodable_type
from eth_account.messages import SignableMessage, hash_domain, hash_eip712_message
from eth_utils.curried import ValidationError
from hexbytes import HexBytes

# ! Do not change the order of the fields in this list !
# To correctly encode and hash the domain fields, they
# must be in this precise order.
EIP712_DOMAIN_FIELDS = {
    "name": "string",
    "version": "string",
    "chainId": "uint256",
    "verifyingContract": "address",
    "salt": "bytes32",
}

EIP712_BODY_FIELDS = [
    "types",
    "primaryType",
    "domain",
    "message",
]


@dataclass(iter=True, slots=True, kwargs=True, kw_only=True)
class EIP712Type:
    """
    Dataclass for `EIP-712 <https://eips.ethereum.org/EIPS/eip-712>`__ structured data types
    (i.e. the contents of an :class:`EIP712Message`).
    """

    def __repr__(self) -> str:
        return self.__class__.__name__

    @property
    def _types_(self) -> dict:
        """
        Recursively built ``dict`` (name of type ``->`` list of subtypes) of
        the underlying fields' types.
        """
        types: Dict[str, list] = {repr(self): []}

        for field in fields(self.__class__):
            value = getattr(self, field)
            if isinstance(value, EIP712Type):
                types[repr(self)].append({"name": field, "type": repr(value)})
                types.update(value._types_)
            else:
                # TODO: Use proper ABI typing, not strings
                field_type = self.__annotations__[field]

                if isinstance(field_type, str):
                    if not is_encodable_type(field_type):
                        raise ValidationError(f"'{field}: {field_type}' is not a valid ABI type")

                elif issubclass(field_type, EIP712Type):
                    field_type = repr(field_type)

                else:
                    raise ValidationError(
                        f"'{field}' type annotation must either be a subclass of "
                        f"`EIP712Type` or valid ABI Type string, not {field_type.__name__}"
                    )

                types[repr(self)].append({"name": field, "type": field_type})

        return types

    def __getitem__(self, key: str) -> Any:
        if (key.startswith("_") and key.endswith("_")) or key not in fields(self.__class__):
            raise KeyError("Cannot look up header fields or other attributes this way")

        return getattr(self, key)


class EIP712Message(EIP712Type):
    """
    Container for EIP-712 messages with type information, domain separator
    parameters, and the message object.
    """

    # NOTE: Must override at least one of these fields
    _name_: Optional[str] = None
    _version_: Optional[str] = None
    _chainId_: Optional[int] = None
    _verifyingContract_: Optional[str] = None
    _salt_: Optional[bytes] = None

    def __post_init__(self):
        # At least one of the header fields must be in the EIP712 message header
        if not any(getattr(self, f"_{field}_") for field in EIP712_DOMAIN_FIELDS):
            raise ValidationError(
                f"EIP712 Message definition '{repr(self)}' must define "
                f"at least one of: _{'_, _'.join(EIP712_DOMAIN_FIELDS)}_"
            )

    @property
    def _domain_(self) -> dict:
        """The EIP-712 domain structure to be used for serialization and hashing."""
        domain_type = [
            {"name": field, "type": abi_type}
            for field, abi_type in EIP712_DOMAIN_FIELDS.items()
            if getattr(self, f"_{field}_")
        ]
        return {
            "types": {
                "EIP712Domain": domain_type,
            },
            "domain": {field["name"]: getattr(self, f"_{field['name']}_") for field in domain_type},
        }

    @property
    def _body_(self) -> dict:
        """The EIP-712 structured message to be used for serialization and hashing."""
        return {
            "domain": self._domain_["domain"],
            "types": dict(self._types_, **self._domain_["types"]),
            "primaryType": repr(self),
            "message": {
                key: getattr(self, key)
                for key in fields(self.__class__)
                if not key.startswith("_") or not key.endswith("_")
            },
        }

    def __getitem__(self, key: str) -> Any:
        if key in EIP712_BODY_FIELDS:
            return self._body_[key]

        return super().__getitem__(key)

    @property
    def signable_message(self) -> SignableMessage:
        """The current message as a :class:`SignableMessage` named tuple instance."""
        return SignableMessage(
            HexBytes(b"\x01"),
            HexBytes(hash_domain(self._domain_)),
            HexBytes(hash_eip712_message(self._body_)),
        )
