import pytest
from eth_utils import to_hex

from eip712.messages import calculate_hash

from .conftest import (
    MainType,
    MessageWithCanonicalDomainFieldOrder,
    MessageWithNonCanonicalDomainFieldOrder,
)


def test_nested_list_message(main_instance):
    assert main_instance._types_ == {
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
    assert main_instance._body_.get("message") == {
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


def test_invalid_message_without_domain_fields():
    with pytest.raises(TypeError):
        MainType(age=30, nested=[])


def test_multilevel_message(valid_message_with_name_domain_field):
    msg = valid_message_with_name_domain_field.signable_message
    assert to_hex(msg.version) == "0x01"
    assert (
        to_hex(msg.header) == "0x336a9d2b32d1ab7ea7bbbd2565eca1910e54b74843858dec7a81f772a3c17e17"
    )
    assert to_hex(msg.body) == "0x306af87567fa87e55d2bd925d9a3ed2b1ec2c3e71b142785c053dc60b6ca177b"


def test_yearn_vaults_message(permit, permit_raw_data):
    """
    Testing a real world EIP712 message for a "permit" call in yearn-vaults.
    """

    assert permit._body_ == permit_raw_data


def test_eip712_domain_field_order_is_invariant():
    assert (
        MessageWithCanonicalDomainFieldOrder._domain_
        == MessageWithNonCanonicalDomainFieldOrder._domain_
    )


def test_ux_tuple_and_starargs(permit, Permit):
    assert tuple(Permit(*permit)) == tuple(permit)
