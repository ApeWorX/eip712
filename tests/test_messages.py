import pytest

from eip712.messages import EIP712Message, EIP712Type, ValidationError


class SubType(EIP712Type):
    inner: "uint256"  # type: ignore # noqa: F821


class ValidMessageWithNameDomainField(EIP712Message):
    _name_: "string" = "Valid Test Message"  # type: ignore # noqa: F821
    value: "uint256"  # type: ignore # noqa: F821
    default_value: "address" = "0xFFfFfFffFFfffFFfFFfFFFFFffFFFffffFfFFFfF"  # type: ignore # noqa: F821,E501
    sub: SubType


class InvalidMessageMissingDomainFields(EIP712Message):
    value: "uint256"  # type: ignore # noqa: F821


def test_multilevel_message():
    msg = ValidMessageWithNameDomainField(value=1, sub=SubType(inner=2))

    assert msg.version.hex() == "01"
    assert msg.header.hex() == "336a9d2b32d1ab7ea7bbbd2565eca1910e54b74843858dec7a81f772a3c17e17"
    assert msg.body.hex() == "306af87567fa87e55d2bd925d9a3ed2b1ec2c3e71b142785c053dc60b6ca177b"


def test_invalid_message_without_domain_fields():
    with pytest.raises(ValidationError):
        InvalidMessageMissingDomainFields(value=1)


def test_yearn_vaults_message():
    """
    Testing a real world EIP712 message for a "permit" call in yearn-vaults.
    """

    class Permit(EIP712Message):
        _name_: "string" = "Yearn Vault"  # type: ignore # noqa: F821
        _version_: "string"  # type: ignore # noqa: F821
        _chainId_: "uint256"  # type: ignore # noqa: F821
        _verifyingContract_: "address"  # type: ignore # noqa: F821

        owner: "address"  # type: ignore # noqa: F821
        spender: "address"  # type: ignore # noqa: F821
        value: "uint256"  # type: ignore # noqa: F821
        nonce: "uint256"  # type: ignore # noqa: F821
        deadline: "uint256"  # type: ignore # noqa: F821

    name = "Yearn Vault"
    version = "0.3.5"
    chain_id = 1
    vault_address = "0x1596Ff8ED308a83897a731F3C1e814B19E11D68c"
    owner_address = "0xf5a2f086cCB7eec82d10bc3600932E9f78d0B212"
    spender_address = "0x1CEE82EEd89Bd5Be5bf2507a92a755dcF1D8e8dc"
    allowance = 100
    nonce = 0
    deadline = 1619151069
    permit = Permit(
        _name_=name,
        _version_=version,
        _chainId_=chain_id,
        _verifyingContract_=vault_address,
        owner=owner_address,
        spender=spender_address,
        value=allowance,
        nonce=nonce,
        deadline=deadline,
    )

    # taken from https://github.com/yearn/yearn-vaults/blob/67cf46f3/tests/conftest.py#L144-L190
    data = {
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
            "name": name,
            "version": version,
            "chainId": chain_id,
            "verifyingContract": vault_address,
        },
        "primaryType": "Permit",
        "message": {
            "owner": owner_address,
            "spender": spender_address,
            "value": allowance,
            "nonce": nonce,
            "deadline": deadline,
        },
    }

    assert permit.body_data == data
