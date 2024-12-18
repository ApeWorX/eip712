# flake8: noqa F821
# Collection of commonly-used EIP712 message type definitions
from typing import Optional, Type, Union

from eth_pydantic_types.abi import address, bytes, bytes32, string, uint8, uint256

from .messages import EIP712Message


class EIP2612(EIP712Message):
    # NOTE: Subclass this w/ at least one header field

    owner: address
    spender: address
    value: uint256
    nonce: uint256
    deadline: uint256


class EIP4494(EIP712Message):
    # NOTE: Subclass this w/ at least one header field

    spender: address
    tokenId: uint256
    nonce: uint256
    deadline: uint256


def create_permit_def(eip=2612, **header_fields):
    if eip == 2612:

        class Permit(EIP2612):
            eip712_name_: Optional[string] = header_fields.get("name", None)
            eip712_version_: Optional[string] = header_fields.get("version", None)
            eip712_chainId_: Optional[uint256] = header_fields.get("chainId", None)
            eip712_verifyingContract_: Optional[string] = header_fields.get(
                "verifyingContract", None
            )
            eip712_salt_: Optional[bytes32] = header_fields.get("salt", None)

    elif eip == 4494:

        class Permit(EIP4494):
            eip712_name_: Optional[string] = header_fields.get("name", None)
            eip712_version_: Optional[string] = header_fields.get("version", None)
            eip712_chainId_: Optional[uint256] = header_fields.get("chainId", None)
            eip712_verifyingContract_: Optional[string] = header_fields.get(
                "verifyingContract", None
            )
            eip712_salt_: Optional[bytes32] = header_fields.get("salt", None)

    else:
        raise ValueError(f"Invalid eip {eip}, must use one of: {EIP2612}, {EIP4494}")

    return Permit


class SafeTxV1(EIP712Message):
    # NOTE: Subclass this as `SafeTx` w/ at least one header field
    to: address
    value: uint256 = 0
    data: bytes = b""
    operation: uint8 = 0
    safeTxGas: uint256 = 0
    dataGas: uint256 = 0
    gasPrice: uint256 = 0
    gasToken: address = "0x0000000000000000000000000000000000000000"
    refundReceiver: address = "0x0000000000000000000000000000000000000000"
    nonce: uint256


class SafeTxV2(EIP712Message):
    # NOTE: Subclass this as `SafeTx` w/ at least one header field
    to: address
    value: uint256 = 0
    data: bytes = b""
    operation: uint8 = 0
    safeTxGas: uint256 = 0
    baseGas: uint256 = 0
    gasPrice: uint256 = 0
    gasToken: address = "0x0000000000000000000000000000000000000000"
    refundReceiver: address = "0x0000000000000000000000000000000000000000"
    nonce: uint256


SafeTx = Union[SafeTxV1, SafeTxV2]
SAFE_VERSIONS = {"1.0.0", "1.1.0", "1.1.1", "1.2.0", "1.3.0"}


def create_safe_tx_def(
    version: str = "1.3.0",
    contract_address: Optional[str] = None,
    chain_id: Optional[int] = None,
) -> type[SafeTx]:
    if not contract_address:
        raise ValueError("Must define 'contract_address'")

    if version not in SAFE_VERSIONS:
        raise ValueError(f"Unknown version {version}")

    major, minor, patch = map(int, version.split("."))

    if minor < 3:

        class SafeTx(SafeTxV1):
            eip712_verifyingContract_: address = contract_address

    elif not chain_id:
        raise ValueError("Must supply 'chain_id=' for Safe versions 1.3.0 or later")

    else:

        class SafeTx(SafeTxV2):  # type: ignore[no-redef]
            eip712_chainId_: uint256 = chain_id
            eip712_verifyingContract_: address = contract_address

    return SafeTx
