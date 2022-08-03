import pytest

from eip712.messages import EIP712Message, EIP712Type

PERMIT_NAME = "Yearn Vault"
PERMIT_VERSION = "0.3.5"
PERMIT_CHAIN_ID = 1
PERMIT_VAULT_ADDRESS = "0x1596Ff8ED308a83897a731F3C1e814B19E11D68c"
PERMIT_OWNER_ADDRESS = "0xf5a2f086cCB7eec82d10bc3600932E9f78d0B212"
PERMIT_SPENDER_ADDRESS = "0x1CEE82EEd89Bd5Be5bf2507a92a755dcF1D8e8dc"
PERMIT_ALLOWANCE = 100
PERMIT_NONCE = 0
PERMIT_DEADLINE = 1619151069


class SubType(EIP712Type):
    inner: "uint256"  # type: ignore


class ValidMessageWithNameDomainField(EIP712Message):
    _name_: "string" = "Valid Test Message"  # type: ignore
    value: "uint256"  # type: ignore
    default_value: "address" = "0xFFfFfFffFFfffFFfFFfFFFFFffFFFffffFfFFFfF"  # type: ignore
    sub: SubType


class MessageWithInvalidNameType(EIP712Message):
    _name_: str = "Invalid Test Message"  # type: ignore


class InvalidMessageMissingDomainFields(EIP712Message):
    value: "uint256"  # type: ignore


class Permit(EIP712Message):
    _name_: "string" = PERMIT_NAME  # type: ignore
    _version_: "string"  # type: ignore
    _chainId_: "uint256"  # type: ignore
    _verifyingContract_: "address"  # type: ignore

    owner: "address"  # type: ignore
    spender: "address"  # type: ignore
    value: "uint256"  # type: ignore
    nonce: "uint256"  # type: ignore
    deadline: "uint256"  # type: ignore


@pytest.fixture
def valid_message_with_name_domain_field():
    return ValidMessageWithNameDomainField(value=1, sub=SubType(inner=2))


@pytest.fixture
def permit():
    return Permit(
        _name_=PERMIT_NAME,
        _version_=PERMIT_VERSION,
        _chainId_=PERMIT_CHAIN_ID,
        _verifyingContract_=PERMIT_VAULT_ADDRESS,
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
