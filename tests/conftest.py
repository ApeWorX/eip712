from typing import TYPE_CHECKING

import pytest
from hexbytes import HexBytes

from eip712.common import create_permit_def
from eip712.messages import EIP712Message, EIP712Type

if TYPE_CHECKING:
    from eth_pydantic_types.abi import address, bytes32, string, uint256

PERMIT_NAME = "Yearn Vault"
PERMIT_VERSION = "0.3.5"
PERMIT_CHAIN_ID = 1
PERMIT_VAULT_ADDRESS = "0x1596Ff8ED308a83897a731F3C1e814B19E11D68c"
PERMIT_OWNER_ADDRESS = "0xf5a2f086cCB7eec82d10bc3600932E9f78d0B212"
PERMIT_SPENDER_ADDRESS = "0x1CEE82EEd89Bd5Be5bf2507a92a755dcF1D8e8dc"
PERMIT_ALLOWANCE = 100
PERMIT_NONCE = 0
PERMIT_DEADLINE = 1619151069
PERMIT_SALT = HexBytes(123456789)


class SubType(EIP712Type):
    inner: "uint256"


class ValidMessageWithNameDomainField(EIP712Message):
    eip712_name_: "string" = "Valid Test Message"
    value: "uint256"
    default_value: "address" = "0xFFfFfFffFFfffFFfFFfFFFFFffFFFffffFfFFFfF"
    sub: SubType


class MessageWithNonCanonicalDomainFieldOrder(EIP712Message):
    eip712_name_: "string" = PERMIT_NAME
    eip712_salt_: "bytes32" = PERMIT_SALT
    eip712_chainId_: "uint256" = PERMIT_CHAIN_ID
    eip712_version_: "string" = PERMIT_VERSION
    eip712_verifyingContract_: "address" = PERMIT_VAULT_ADDRESS


class MessageWithCanonicalDomainFieldOrder(EIP712Message):
    eip712_name_: "string" = PERMIT_NAME
    eip712_version_: "string" = PERMIT_VERSION
    eip712_chainId_: "uint256" = PERMIT_CHAIN_ID
    eip712_verifyingContract_: "address" = PERMIT_VAULT_ADDRESS
    eip712_salt_: "bytes32" = PERMIT_SALT


class InvalidMessageMissingDomainFields(EIP712Message):
    value: "uint256"


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
