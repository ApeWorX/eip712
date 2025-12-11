"""
Message classes for typed structured data hashing and signing in Ethereum.
"""

from typing import Any, ClassVar

from eth_account._utils.encode_typed_data.encoding_and_hashing import encode_data, hash_type
from eth_account.messages import (
    SignableMessage,
    encode_typed_data,
    get_primary_type,
    hash_domain,
    hash_eip712_message,
)
from eth_pydantic_types import HexBytes, abi
from eth_utils import keccak
from eth_utils.crypto import keccak
from pydantic import BaseModel, ConfigDict, PrivateAttr

from .utils import build_eip712_type

# NOTE: For backwards compatibility purposes
# TODO: Remove in v1
EIP712Type = BaseModel


class EIP712Domain(BaseModel):
    # NOTE: Do not change the order of the fields in this list!
    #       To correctly encode and hash the domain fields, they must be in this precise order.
    name: abi.string | None = None
    version: abi.string | None = None
    chainId: abi.uint256 | None = None
    verifyingContract: abi.address | None = None
    salt: abi.bytes32 | None = None

    @property
    def eip712_type(self) -> dict:
        return dict(
            EIP712Domain=[
                {"name": field, "type": field_info.annotation.__args__[0].__name__}
                for field, field_info in self.model_fields.items()
                if getattr(self, field) is not None
            ]
        )


class EIP712Message(BaseModel):
    """
    Container for EIP-712 messages with type information, domain separator
    parameters, and the message object.
    """

    eip712_domain: ClassVar[EIP712Domain | None] = None

    _eip712_domain_: EIP712Domain = PrivateAttr()

    model_config = ConfigDict(extra="allow")

    def model_post_init(self, context: Any):
        """The EIP-712 domain structure to be used for serialization and hashing."""

        if self.eip712_domain:
            self._eip712_domain_ = self.eip712_domain
            return

        if not self.__pydantic_extra__:
            model_fields = "', '".join(EIP712Domain.model_fields)
            raise TypeError(f"Must define at least one domain field: '{model_fields}")

        self._eip712_domain_ = EIP712Domain(
            **{
                field: self.__pydantic_extra__.pop(field, None)
                for field in EIP712Domain.model_fields
            }
        )

    def __iter__(self):
        # NOTE: We override this to get nice behavior in Ape transaction methods
        return (v for _, v in super().__iter__())

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
        return encode_typed_data(full_message=extract_eip712_struct_message(self))


def extract_eip712_struct_message(msg: EIP712Message) -> dict:
    """The EIP-712 structured message to be used for serialization and hashing."""

    return {
        "domain": msg._eip712_domain_.model_dump(exclude_none=True),
        "types": {**msg._eip712_domain_.eip712_type, **build_eip712_type(msg.__class__)},
        "primaryType": msg.__class__.__name__,
        "message": msg.model_dump(),
    }


def calculate_hash(msg: SignableMessage) -> HexBytes:
    return HexBytes(keccak(b"".join([bytes.fromhex("19"), *msg])))
