from eth_pydantic_types import abi  # noqa: TC002
from pydantic import create_model

from .messages import EIP712Domain, EIP712Message


class EIP2612(EIP712Message):
    owner: abi.address
    spender: abi.address
    value: abi.uint256
    nonce: abi.uint256
    deadline: abi.uint256


class EIP4494(EIP712Message):
    spender: abi.address
    tokenId: abi.uint256
    nonce: abi.uint256
    deadline: abi.uint256


def create_permit_def(eip=2612, **header_fields):
    if eip == 2612:
        Permit = create_model("Permit", __base__=EIP2612)

    elif eip == 4494:
        Permit = create_model("Permit", __base__=EIP4494)

    else:
        raise ValueError(f"Invalid eip {eip}, must use one of: {EIP2612}, {EIP4494}")

    Permit.eip712_domain = EIP712Domain(**header_fields)
    return Permit


ZERO_ADDRESS: abi.address = "0x0000000000000000000000000000000000000000"  # type: ignore[assignment]


class SafeTxV1(EIP712Message):
    # NOTE: Subclass this as `SafeTx` w/ at least one header field
    to: abi.address
    value: abi.uint256 = 0
    data: abi.bytes = b""
    operation: abi.uint8 = 0
    safeTxGas: abi.uint256 = 0
    dataGas: abi.uint256 = 0
    gasPrice: abi.uint256 = 0
    gasToken: abi.address = ZERO_ADDRESS
    refundReceiver: abi.address = ZERO_ADDRESS
    nonce: abi.uint256


class SafeTxV2(EIP712Message):
    # NOTE: Subclass this as `SafeTx` w/ at least one header field
    to: abi.address
    value: abi.uint256 = 0
    data: abi.bytes = b""
    operation: abi.uint8 = 0
    safeTxGas: abi.uint256 = 0
    baseGas: abi.uint256 = 0
    gasPrice: abi.uint256 = 0
    gasToken: abi.address = ZERO_ADDRESS
    refundReceiver: abi.address = ZERO_ADDRESS
    nonce: abi.uint256


SafeTx = SafeTxV1 | SafeTxV2
SAFE_VERSIONS = {"1.0.0", "1.1.0", "1.1.1", "1.2.0", "1.3.0", "1.4.1"}


def create_safe_tx_def(
    version: str = "1.3.0",
    contract_address: abi.address | None = None,
    chain_id: abi.uint256 | None = None,
) -> type[SafeTx]:
    if not contract_address:
        raise ValueError("Must define 'contract_address'")

    if version not in SAFE_VERSIONS:
        raise ValueError(f"Unknown version {version}")

    major, minor, _ = map(int, version.split("."))

    if major == 1 and minor < 3:
        SafeTx = create_model("SafeTx", __base__=SafeTxV1)
        SafeTx.eip712_domain = EIP712Domain(verifyingContract=contract_address)

    elif not chain_id:
        raise ValueError("Must supply 'chain_id=' for Safe versions 1.3.0 or later")

    else:
        SafeTx = create_model("SafeTx", __base__=SafeTxV2)  # type: ignore[arg-type]
        SafeTx.eip712_domain = EIP712Domain(verifyingContract=contract_address, chainId=chain_id)

    return SafeTx
