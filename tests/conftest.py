import pytest
from eth_pydantic_types import abi  # noqa: TC002
from hexbytes import HexBytes

from eip712.common import create_permit_def
from eip712.messages import EIP712Domain, EIP712Message, EIP712Type
from eip712.utils import SUPPORTED_NONABI_TYPES

PERMIT_NAME = "Yearn Vault"
PERMIT_VERSION = "0.3.5"
PERMIT_CHAIN_ID = 1
PERMIT_VAULT_ADDRESS = "0x1596Ff8ED308a83897a731F3C1e814B19E11D68c"
PERMIT_OWNER_ADDRESS = "0xf5a2f086cCB7eec82d10bc3600932E9f78d0B212"
PERMIT_SPENDER_ADDRESS = "0x1CEE82EEd89Bd5Be5bf2507a92a755dcF1D8e8dc"
PERMIT_ALLOWANCE = 100
PERMIT_NONCE = 0
PERMIT_DEADLINE = 1619151069
PERMIT_SALT = "0x" + (HexBytes(123456789) + HexBytes(b"\x00" * 28)).hex()

ALL_SUPPORTED_TYPES: list = [abi.address, abi.string]
ALL_SUPPORTED_TYPES.extend(getattr(abi, t) for t in (f"uint{i}" for i in range(8, 256 + 8, 8)))
ALL_SUPPORTED_TYPES.extend(getattr(abi, t) for t in (f"int{i}" for i in range(8, 256 + 8, 8)))
ALL_SUPPORTED_TYPES.extend(getattr(abi, t) for t in (f"bytes{i}" for i in range(1, 32 + 1)))
ALL_SUPPORTED_TYPES.extend(SUPPORTED_NONABI_TYPES)

# dynamic-sized arrays of other types (`list[T]` is a shortcut for dynamic arrays)
# NOTE: **Important** DO NOT REMOVE WRAPPING BRACKETS (causes infinite alloc loop)
ALL_SUPPORTED_TYPES.extend([list[t] for t in ALL_SUPPORTED_TYPES])  # type: ignore[valid-type]

# TODO: Support static arrays


class SubType(EIP712Type):
    inner: abi.uint256


class ValidMessageWithNameDomainField(EIP712Message):
    eip712_domain = EIP712Domain(name="Valid Test Message")

    value: abi.uint256
    default_value: abi.address = "0xFFfFfFffFFfffFFfFFfFFFFFffFFFffffFfFFFfF"  # type: ignore[assignment]
    sub: SubType


class InvalidMessageMissingDomainFields(EIP712Message):
    value: abi.uint256


class NestedType(EIP712Type):
    field1: abi.string
    field2: abi.uint256


class MainType(EIP712Message):
    eip712_domain = EIP712Domain(name="MainType", version="1")

    name: abi.string
    age: abi.uint256
    nested: list[NestedType]


@pytest.fixture
def nested_instance_1():
    return NestedType(field1="nested1", field2=100)


@pytest.fixture
def nested_instance_2():
    return NestedType(field1="nested2", field2=200)


@pytest.fixture
def main_instance(nested_instance_1, nested_instance_2):
    return MainType(name="Alice", age=30, nested=[nested_instance_1, nested_instance_2])


@pytest.fixture
def valid_message_with_name_domain_field():
    return ValidMessageWithNameDomainField(value=1, sub=SubType(inner=2))


@pytest.fixture
def Permit():
    return create_permit_def(
        name=PERMIT_NAME,
        version=PERMIT_VERSION,
        chainId=PERMIT_CHAIN_ID,
        verifyingContract=PERMIT_VAULT_ADDRESS,
        salt=PERMIT_SALT,
    )


@pytest.fixture
def permit(Permit):
    return Permit(
        owner=PERMIT_OWNER_ADDRESS,
        spender=PERMIT_SPENDER_ADDRESS,
        value=PERMIT_ALLOWANCE,
        nonce=PERMIT_NONCE,
        deadline=PERMIT_DEADLINE,
    )


@pytest.fixture
def permit_raw_data():
    # taken from https://github.com/yearn/yearn-vaults/blob/67cf46f3/tests/conftest.py#L144-L190
    return {
        "types": {
            "EIP712Domain": [
                {"name": "name", "type": "string"},
                {"name": "version", "type": "string"},
                {"name": "chainId", "type": "uint256"},
                {"name": "verifyingContract", "type": "address"},
                {"name": "salt", "type": "bytes32"},
            ],
            "Permit": [
                {"name": "owner", "type": "address"},
                {"name": "spender", "type": "address"},
                {"name": "value", "type": "uint256"},
                {"name": "nonce", "type": "uint256"},
                {"name": "deadline", "type": "uint256"},
            ],
        },
        "domain": {
            "name": PERMIT_NAME,
            "version": PERMIT_VERSION,
            "chainId": PERMIT_CHAIN_ID,
            "verifyingContract": PERMIT_VAULT_ADDRESS,
            "salt": PERMIT_SALT,
        },
        "primaryType": "Permit",
        "message": {
            "owner": PERMIT_OWNER_ADDRESS,
            "spender": PERMIT_SPENDER_ADDRESS,
            "value": PERMIT_ALLOWANCE,
            "nonce": PERMIT_NONCE,
            "deadline": PERMIT_DEADLINE,
        },
    }
