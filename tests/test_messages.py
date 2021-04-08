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
