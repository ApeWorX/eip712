"""
Message classes for typed structured data hashing and signing in Ethereum.
"""

from typing import TYPE_CHECKING, Any, Optional, get_args, get_origin

from eth_abi.abi import is_encodable_type  # type: ignore[import-untyped]
from eth_account._utils.encode_typed_data.encoding_and_hashing import encode_data, hash_type
from eth_account.messages import SignableMessage, get_primary_type, hash_domain, hash_eip712_message
from eth_pydantic_types import Address, HexBytes
from eth_utils import keccak
from eth_utils.curried import ValidationError
from pydantic import BaseModel, model_validator
from typing_extensions import _AnnotatedAlias

if TYPE_CHECKING:
    from eth_pydantic_types.abi import bytes32, string, uint256

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


class EIP712Type(BaseModel):
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

        for field in {
            k: v.annotation.__name__ # type: ignore[union-attr]
            for k, v in self.model_fields.items()
            if not k.startswith("eip712_")
        }:
            value = getattr(self, field)
            if isinstance(value, EIP712Type):
                types[repr(self)].append({"name": field, "type": repr(value)})
                types.update(value._types_)
            else:
                field_type = search_annotations(self, field)

                # If the field type is a string, validate through eth-abi
                if isinstance(field_type, str):
                    if not is_encodable_type(field_type):
                        raise ValidationError(f"'{field}: {field_type}' is not a valid ABI Type")

                elif isinstance(field_type, type) and issubclass(field_type, EIP712Type):
                    field_type = repr(field_type)

                else:
                    try:
                        # If field type already has validators or is a known type
                        #  can confirm that type name will be correct
                        if isinstance(field_type.__value__, _AnnotatedAlias) or issubclass(
                            field_type.__value__, (Address, HexBytes)
                        ):
                            field_type = field_type.__name__

                    except AttributeError:
                        raise ValidationError(
                            f"'{field}' type annotation must either be a subclass of "
                            f"`EIP712Type` or valid ABI Type, not {field_type.__name__}"
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
        if (key.startswith("eip712_") and key.endswith("_")) or key not in self.model_fields:
            raise KeyError("Cannot look up header fields or other attributes this way")

        return getattr(self, key)

    def _prepare_data_for_hashing(self, data: dict) -> dict:
        result: dict = {}

        for key, value in data.items():
            item: Any = value
            if isinstance(value, EIP712Type):
                item = value.model_dump(mode="json")
            elif isinstance(value, dict):
                item = self._prepare_data_for_hashing(item)

            result[key] = item

        return result


class EIP712Message(EIP712Type):
    """
    Container for EIP-712 messages with type information, domain separator
    parameters, and the message object.
    """

    # NOTE: Must override at least one of these fields
    eip712_name_: "string | None" = None
    eip712_version_: "string | None" = None
    eip712_chainId_: "uint256 | None" = None
    eip712_verifyingContract_: "string | None" = None
    eip712_salt_: "bytes32 | None" = None

    @model_validator(mode="after")
    @classmethod
    def validate_model(cls, value):
        # At least one of the header fields must be in the EIP712 message header
        if not any(f"eip712_{field}_" in value.__annotations__ for field in EIP712_DOMAIN_FIELDS):
            raise ValidationError(
                f"EIP712 Message definition '{repr(cls)}' must define "
                f"at least one of: eip712_{'_, eip712_'.join(EIP712_DOMAIN_FIELDS)}_"
            )
        return value

    @property
    def _domain_(self) -> dict:
        """The EIP-712 domain structure to be used for serialization and hashing."""
        domain_type = [
            {"name": field, "type": abi_type}
            for field, abi_type in EIP712_DOMAIN_FIELDS.items()
            if getattr(self, f"eip712_{field}_")
        ]
        return {
            "types": {
                "EIP712Domain": domain_type,
            },
            "domain": {
                field["name"]: getattr(self, f"eip712_{field['name']}_") for field in domain_type
            },
        }

    @property
    def _body_(self) -> dict:
        """The EIP-712 structured message to be used for serialization and hashing."""
        return {
            "domain": self._domain_["domain"],
            "types": dict(self._types_, **self._domain_["types"]),
            "primaryType": repr(self),
            "message": {
                # TODO use __pydantic_extra__ instead
                key: getattr(self, key)
                for key in self.model_fields
                if not key.startswith("eip712_") or not key.endswith("_")
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
        domain = self._prepare_data_for_hashing(self._domain_["domain"])
        types = self._prepare_data_for_hashing(self._types_)
        message = self._prepare_data_for_hashing(self._body_["message"])
        messagebytes = HexBytes(1)
        messageDomain = HexBytes(hash_domain(domain))
        messageEIP = HexBytes(hash_eip712_message(types, message))
        return SignableMessage(
            messagebytes,
            messageDomain,
            messageEIP,
        )


def calculate_hash(msg: SignableMessage) -> HexBytes:
    return HexBytes(keccak(b"".join([bytes.fromhex("19"), *msg])))


def search_annotations(cls, field: str) -> Any:
    if hasattr(cls, "__annotations__") and field in cls.__annotations__:
        return cls.__annotations__[field]
    return search_annotations(super(cls.__class__, cls), field)
