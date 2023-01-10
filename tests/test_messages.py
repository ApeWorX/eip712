import pytest
from hexbytes import HexBytes

from eip712.common import SAFE_VERSIONS, create_safe_tx_def
from eip712.hashing import hash_message
from eip712.messages import ValidationError

from .conftest import (
    InvalidMessageMissingDomainFields,
    MessageWithCanonicalDomainFieldOrder,
    MessageWithNonCanonicalDomainFieldOrder,
)


def test_multilevel_message(valid_message_with_name_domain_field):
    msg = valid_message_with_name_domain_field.signable_message
    assert msg.version == HexBytes("0x01")
    assert msg.header == HexBytes(
        "0x336a9d2b32d1ab7ea7bbbd2565eca1910e54b74843858dec7a81f772a3c17e17"
    )
    assert msg.body == HexBytes(
        "0x306af87567fa87e55d2bd925d9a3ed2b1ec2c3e71b142785c053dc60b6ca177b"
    )


def test_invalid_message_without_domain_fields():
    with pytest.raises(ValidationError):
        InvalidMessageMissingDomainFields(value=1)


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


MSIG_ADDRESS = "0xFEB4acf3df3cDEA7399794D0869ef76A6EfAff52"


@pytest.mark.parametrize("version", SAFE_VERSIONS)
def test_gnosis_safe_tx(version):
    tx_def = create_safe_tx_def(
        version=version,
        contract_address=MSIG_ADDRESS,
        chain_id=1,
    )

    msg = tx_def(MSIG_ADDRESS, 0, b"", 0, 0, 0, 0, MSIG_ADDRESS, MSIG_ADDRESS, 0)

    assert msg.signable_message.header.hex() == (
        "88fbc465dedd7fe71b7baef26a1f46cdaadd50b95c77cbe88569195a9fe589ab"
        if version in ("1.3.0",)
        else "590e9c66b22ee4584cd655fda57748ce186b85f829a092c28209478efbe86a92"
    )

    assert hash_message(msg).hex() == (
        "52307871756d6c59b490297be3f13178c9b61c57560fd37de628733ac673769e"
        if version in ("1.3.0",)
        else "70ae0b149c9dd8329c0234dbcb63993d350450049fdfd3d1c9ce19a93cc5afa5"
    )
