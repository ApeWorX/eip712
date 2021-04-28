# This is needed otherwise "string", "uint256" get marked as failing type
# annotations (the types aren't defined anywhere).
# flake8: noqa

from eip712.messages import EIP712Message, EIP712Type


class SubType(EIP712Type):
    inner: "uint256"  # type: ignore


class ValidMsgDef(EIP712Message):
    _name_: "string" = "Name"  # type: ignore

    value: "uint256"  # type: ignore
    default_value: "address" = "0xFFfFfFffFFfffFFfFFfFFFFFffFFFffffFfFFFfF"  # type: ignore
    sub: SubType


def test_multilevel_message():
    msg = ValidMsgDef(value=1, sub=SubType(inner=2))

    assert msg.version.hex() == "01"
    assert msg.header.hex() == "ae5d5ac778a755034e549ed137af5f5bf0aacf767321bb6127ec8a1e8c68714b"
    assert msg.body.hex() == "bbc572c6c3273deb6d95ffae1b79c35452b4996b81aa243b17eced03c0b01c54"


def test_yearn_vaults_message():
    """
    Testing a real world EIP712 message for a "permit" call in yearn-vaults.
    """

    class Permit(EIP712Message):
        _name_: "string" = "Yearn Vault"
        _version_: "string"
        _chainId_: "uint256"
        _verifyingContract_: "address"

        owner: "address"
        spender: "address"
        value: "uint256"
        nonce: "uint256"
        deadline: "uint256"

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
