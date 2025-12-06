"""
Message classes for typed structured data hashing and signing in Ethereum.
"""

from typing import Any, get_args, get_origin

from dataclassy import asdict, dataclass, fields
from eth_abi.abi import is_encodable_type  # type: ignore[import-untyped]
from eth_account._utils.encode_typed_data.encoding_and_hashing import encode_data, hash_type
from eth_account.messages import SignableMessage, get_primary_type, hash_domain, hash_eip712_message
from eth_utils import keccak
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

    @classmethod
    def eip712_types(cls) -> dict:
        """
        Recursively built ``dict`` (name of type ``->`` list of subtypes) of
        the underlying fields' types.
        """
        types: dict[str, list[dict[str, str]]] = {cls.__name__: []}

        for field in fields(cls):
            field_type = cls.__annotations__[field]

            if get_origin(field_type) is list:
                if isinstance(elem_type := get_args(field_type)[0], str):
                    # TODO: Use proper ABI typing, not strings
                    if not is_encodable_type(elem_type):
                        raise ValidationError(
                            f"'{field}: list[{elem_type}]' is not a valid ABI type"
                        )

                    types[cls.__name__].append({"name": field, "type": f"{elem_type}[]"})

                elif issubclass(elem_type, EIP712Type):
                    types[cls.__name__].append({"name": field, "type": f"{elem_type.__name__}[]"})
                    types.update(elem_type.eip712_types())

                else:
                    raise ValidationError(
                        f"'{field}' type annotation must either be a subclass of "
                        f"`EIP712Type` or valid ABI Type string, not list[{elem_type.__name__}]"
                    )

            elif isinstance(field_type, str):
                # TODO: Use proper ABI typing, not strings
                if not is_encodable_type(field_type):
                    raise ValidationError(f"'{field}: {field_type}' is not a valid ABI type")

                types[cls.__name__].append({"name": field, "type": field_type})

            elif issubclass(field_type, EIP712Type):
                types[cls.__name__].append({"name": field, "type": field_type.__name__})
                types.update(field_type.eip712_types())

            else:
                raise ValidationError(
                    f"'{field}' type annotation must either be a subclass of "
                    f"`EIP712Type` or valid ABI Type string, not {field_type.__name__}"
                )

        return types

    @property
    def _types_(self) -> dict:
        return self.__class__.eip712_types()

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
    _name_: str | None = None
    _version_: str | None = None
    _chainId_: int | None = None
    _verifyingContract_: str | None = None
    _salt_: bytes | None = None

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
                field: (
                    # NOTE: Per EIP-712, encode `list[Item]` as
                    #       `list[dict[Field, getattr(Item, Field)] for Field in fields(Item)]`
                    [
                        dict(zip(fields(item.__class__), item.__tuple__))
                        for item in getattr(self, field)
                    ]
                    if isinstance(getattr(self, field), list)
                    and not is_encodable_type(self.__annotations__[field])
                    # NOTE: Arrays of "basic" values just get encoded as a list
                    else getattr(self, field)
                )
                for field in fields(self.__class__)
                if not field.startswith("_") or not field.endswith("_")
            },
        }

    def __getitem__(self, key: str) -> Any:
        if key in EIP712_BODY_FIELDS:
            return self._body_[key]

        return super().__getitem__(key)

    @property
    def _domain_separator_(self) -> HexBytes:
        """
        The hashed domain.
        """
        domain = _prepare_data_for_hashing(self._domain_["domain"])
        return HexBytes(hash_domain(domain))

    @property
    def _struct_hash_(self) -> HexBytes:
        """
        The hashed message.
        """
        types = _prepare_data_for_hashing(self._types_)
        message = _prepare_data_for_hashing(self._body_["message"])
        return HexBytes(hash_eip712_message(types, message))

    @property
    def _encoded_struct_(self) -> HexBytes:
        types = _prepare_data_for_hashing(self._types_)
        message = _prepare_data_for_hashing(self._body_["message"])
        primary_type = get_primary_type(types)
        return HexBytes(encode_data(primary_type, types, message))

    @property
    def _type_hash_(self) -> HexBytes:
        types = _prepare_data_for_hashing(self._types_)
        primary_type = get_primary_type(types)
        return HexBytes(hash_type(primary_type, types))

    @property
    def _message_hash_(self) -> HexBytes:
        return calculate_hash(self.signable_message)

    @property
    def signable_message(self) -> SignableMessage:
        """
        The current message as a :class:`SignableMessage` named tuple instance.
        **NOTE**: The 0x19 prefix is NOT included.
        """
        return SignableMessage(
            HexBytes(1),
            self._domain_separator_,
            self._struct_hash_,
        )


def calculate_hash(msg: SignableMessage) -> HexBytes:
    return HexBytes(keccak(b"".join([bytes.fromhex("19"), *msg])))


def _prepare_data_for_hashing(data: dict) -> dict:
    result: dict = {}

    for key, value in data.items():
        item: Any = value
        if isinstance(value, EIP712Type):
            item = asdict(value)
        elif isinstance(value, dict):
            item = _prepare_data_for_hashing(item)
        elif isinstance(value, list):
            elms = []
            for elm in item:
                if isinstance(elm, dict):
                    elm = _prepare_data_for_hashing(elm)
                elms.append(elm)
            item = elms

        result[key] = item

    return result
