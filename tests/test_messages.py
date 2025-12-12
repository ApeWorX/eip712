import pytest
from eth_utils import to_hex
from pydantic import ValidationError

from eip712.messages import (
    EIP712Domain,
    EIP712Message,
    calculate_hash,
    extract_eip712_struct_message,
)

from .conftest import InvalidMessageMissingDomainFields, MainType


def test_nested_list_message(main_instance):
    struct_msg = extract_eip712_struct_message(main_instance)
    assert struct_msg["domain"] == {
        "name": "MainType",
        "version": "1",
    }
    assert struct_msg["primaryType"] == "MainType"
    assert struct_msg["types"] == {
        "EIP712Domain": [
            {"name": "name", "type": "string"},
            {"name": "version", "type": "string"},
        ],
        "MainType": [
            {"name": "name", "type": "string"},
            {"name": "age", "type": "uint256"},
            {"name": "nested", "type": "NestedType[]"},
        ],
        "NestedType": [
            {"name": "field1", "type": "string"},
            {"name": "field2", "type": "uint256"},
        ],
    }
    assert struct_msg["message"] == {
        "name": main_instance.name,
        "age": main_instance.age,
        "nested": [
            {"field1": main_instance.nested[0].field1, "field2": main_instance.nested[0].field2},
            {"field1": main_instance.nested[1].field1, "field2": main_instance.nested[1].field2},
        ],
    }

    msg = main_instance.signable_message
    assert to_hex(msg.version) == "0x01"
    assert (
        to_hex(msg.header) == "0x0b2559348f55bf512d3cbed07914b9042c10f07034f553a05e0259103cca9156"
    )
    assert to_hex(msg.body) == "0x0802629e7fba836d4ab3791efd660448d4a23371201ed299e3ffd9bdd6adffaf"

    # Verify hash calculation
    message_hash = calculate_hash(msg)
    assert (
        to_hex(message_hash) == "0x2cf8ef0524314a5c218e235d774fb448453b619c124c3bcd66e4b2806291544d"
    )


def test_invalid_nested_message_without_domain_fields():
    with pytest.raises(ValidationError):
        MainType(age=30, nested=[])


def test_multilevel_message(valid_message_with_name_domain_field):
    msg = valid_message_with_name_domain_field.signable_message
    assert to_hex(msg.version) == "0x01"
    assert (
        to_hex(msg.header) == "0x336a9d2b32d1ab7ea7bbbd2565eca1910e54b74843858dec7a81f772a3c17e17"
    )
    assert to_hex(msg.body) == "0x306af87567fa87e55d2bd925d9a3ed2b1ec2c3e71b142785c053dc60b6ca177b"


def test_invalid_message_without_domain_fields():
    with pytest.raises(TypeError):
        InvalidMessageMissingDomainFields(value=1)

    # NOTE: Works if you dynamically provide header fields
    InvalidMessageMissingDomainFields(value=1, eip712_name="Something valid")


def test_yearn_vaults_message(permit, permit_raw_data):
    """
    Testing a real world EIP712 message for a "permit" call in yearn-vaults.
    """

    assert extract_eip712_struct_message(permit) == permit_raw_data


def test_ux_tuple_and_starargs(permit):
    assert (
        [*permit]
        == list(tuple(permit))  # noqa: C414
        == [permit.owner, permit.spender, permit.value, permit.nonce, permit.deadline]
    )


def test_dynamic_eip712_domain():
    class Msg(EIP712Message):
        a: bytes

    with pytest.raises(TypeError):
        Msg(a=b"")

    Msg(a=b"", eip712_domain=EIP712Domain(name="Something"))

    Msg(a=b"", eip712_name="Something")
    Msg(a=b"", eip712_version="1")
    Msg(a=b"", eip712_verifyingContract="0x0000000000000000000000000000000000000000")
    Msg(a=b"", eip712_chainId=1)
    Msg(a=b"", eip712_salt=b"\x00")
