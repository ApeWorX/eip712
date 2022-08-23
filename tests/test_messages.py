import pytest

from eip712.messages import ValidationError

from .conftest import InvalidMessageMissingDomainFields, MessageWithInvalidNameType


def test_multilevel_message(valid_message_with_name_domain_field):
    msg = valid_message_with_name_domain_field
    assert msg.version.hex() == "01"
    assert msg.header.hex() == "336a9d2b32d1ab7ea7bbbd2565eca1910e54b74843858dec7a81f772a3c17e17"
    assert msg.body.hex() == "306af87567fa87e55d2bd925d9a3ed2b1ec2c3e71b142785c053dc60b6ca177b"


def test_invalid_message_without_domain_fields():
    with pytest.raises(ValidationError):
        InvalidMessageMissingDomainFields(value=1)


def test_invalid_type():
    message = MessageWithInvalidNameType()
    expected_error_message = (
        "'_name_' type annotation must either be a subclass of "
        "`EIP712Type` or valid ABI Type string, not str"
    )

    with pytest.raises(ValidationError, match=expected_error_message):
        message.field_type("_name_")


def test_yearn_vaults_message(permit, permit_raw_data):
    """
    Testing a real world EIP712 message for a "permit" call in yearn-vaults.
    """

    assert permit.body_data == permit_raw_data
