"""
Message classes for typed structured data hashing and signing in Ethereum.
"""

from typing import Any, ClassVar, get_args

from eth_account.messages import SignableMessage, encode_typed_data
from eth_pydantic_types import HexBytes, abi
from eth_utils.crypto import keccak
from pydantic import BaseModel, ConfigDict, PrivateAttr, model_validator

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

    @model_validator(mode="after")
    def validate_at_least_one_field_present(self):
        if not (self.name or self.version or self.chainId or self.verifyingContract or self.salt):
            raise ValueError("Must provider at least one header field")

        return self

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

    You **must** provide either a default eip712 domain via ``eip712_domain``,
    or set one via ``eip712_domain=`` in the initialization of your model.
    You can construct a domain dynamically using 1 or more ``eip712_{field_name}=`` fields as well.

    Usage example::

        class Msg(EIP712Message):
            eip712_domain = EIP712Domain(name="Msg protocol")
            a: abi.address

        assert Msg.eip712_domain.name == "Msg protocol"

        msg = Msg(a="0x0000000000000000000000000000000000000000")
        assert msg.eip712_domain.name == "Msg protocol"

        msg = Msg(a="0x0000000000000000000000000000000000000000", eip712_name="Something else")
        assert msg.eip712_domain.name == "Something else"
    """

    eip712_domain: ClassVar[EIP712Domain | None] = None
    """The default EIP712 to use for this model. Can be overriden on model init"""

    _eip712_domain_: EIP712Domain = PrivateAttr()

    model_config = ConfigDict(extra="allow")

    def model_post_init(self, context: Any):
        # Users must either specify via class variable...
        if self.eip712_domain:
            # Use as default...
            self._eip712_domain_ = self.eip712_domain
            # NOTE: The reason we don't override the class variable is it may affect it's
            #       use in other situations/instances. The classvar is merely the "default" domain

            if self.__pydantic_extra__:
                # ...but then override with any extras
                for field in EIP712Domain.model_fields:
                    if field_value := self.__pydantic_extra__.pop(f"eip712_{field}", None):
                        setattr(self._eip712_domain_, field, field_value)

        # ...or via extras on model init
        elif self.__pydantic_extra__ and isinstance(
            eip712_domain := self.__pydantic_extra__.pop("eip712_domain", None),
            EIP712Domain,
        ):
            self._eip712_domain_ = eip712_domain

        elif self.__pydantic_extra__ and (
            eip712_domain_kwargs := {
                field: value
                for field in EIP712Domain.model_fields
                if (value := self.__pydantic_extra__.pop(f"eip712_{field}", None))
            }
        ):
            self._eip712_domain_ = EIP712Domain(**eip712_domain_kwargs)

        else:
            model_fields = "=...', 'eip712_".join(EIP712Domain.model_fields)
            raise TypeError(
                f"Must initialize with at least one domain field: 'eip712_{model_fields}=...',"
                " or using: 'eip712_domain=EIP712Domain(...)'."
            )

    def __iter__(self):
        # NOTE: We override this to get nice behavior in Ape transaction methods
        #       e.g. `contract.method(*msg, ...)`
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
