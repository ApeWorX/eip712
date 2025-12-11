"""
Message classes for typed structured data hashing and signing in Ethereum.
"""

from typing import Any, ClassVar, get_args

from eth_account.messages import SignableMessage, encode_typed_data
from eth_pydantic_types import HexBytes, abi
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
        return {
            "EIP712Domain": [
                {"name": field, "type": inner_type.__name__}
                for field, field_info in self.model_fields.items()
                if getattr(self, field) is not None
                and (inner_type := get_args(field_info.annotation)[0])
            ]
        }


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


def hash_message(msg: EIP712Message) -> HexBytes:
    """
    Hash the given EIP712 Message Struct

    Args:
        msg: (EIP712Message): EIP712 message struct

    Returns:
        HexBytes: 32 byte hash of the message, hashed according to EIP712
    """
    return calculate_hash(msg.signable_message)
