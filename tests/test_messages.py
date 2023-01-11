import pytest

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
    assert msg.version.hex() == "0x01"
    assert msg.header.hex() == "0x336a9d2b32d1ab7ea7bbbd2565eca1910e54b74843858dec7a81f772a3c17e17"
    assert msg.body.hex() == "0x306af87567fa87e55d2bd925d9a3ed2b1ec2c3e71b142785c053dc60b6ca177b"


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

    msg = tx_def(to=MSIG_ADDRESS, nonce=0)

    assert msg.signable_message.header.hex() == (
        "0x88fbc465dedd7fe71b7baef26a1f46cdaadd50b95c77cbe88569195a9fe589ab"
        if version in ("1.3.0",)
        else "0x590e9c66b22ee4584cd655fda57748ce186b85f829a092c28209478efbe86a92"
    )

    assert hash_message(msg).hex() == (
        "0x3c2fdf2ea8af328a67825162e7686000787c5cc9f4b27cb6bfbcaa445b59e2c4"
        if version in ("1.3.0",)
        else "0x1b393826bed1f2297ffc01916f8339892f9a51dc7f35f477b9a5cdd651d28603"
    )
