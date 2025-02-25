import pytest
from eth_utils import to_hex
from hexbytes import HexBytes

from eip712.common import SAFE_VERSIONS, create_safe_tx_def
from eip712.messages import calculate_hash

MAINNET_MSIG_ADDRESS = "0xFEB4acf3df3cDEA7399794D0869ef76A6EfAff52"
GOERLI_MSIG_ADDRESS = "0x3c59eC3912A6A0c8690ec548D87FB55C3Ba62aBa"


@pytest.mark.parametrize("version", SAFE_VERSIONS)
def test_gnosis_safe_tx(version):
    tx_def = create_safe_tx_def(
        version=version,
        contract_address=MAINNET_MSIG_ADDRESS,
        chain_id=1,
    )

    msg = tx_def(to=MAINNET_MSIG_ADDRESS, nonce=0)

    assert to_hex(msg.signable_message.header) == (
        "0x88fbc465dedd7fe71b7baef26a1f46cdaadd50b95c77cbe88569195a9fe589ab"
        if version in ("1.3.0", "1.4.1")
        else "0x590e9c66b22ee4584cd655fda57748ce186b85f829a092c28209478efbe86a92"
    )

    assert to_hex(msg.signable_message.body) == (
        "0x3c2fdf2ea8af328a67825162e7686000787c5cc9f4b27cb6bfbcaa445b59e2c4"
        if version in ("1.3.0", "1.4.1")
        else "0x1b393826bed1f2297ffc01916f8339892f9a51dc7f35f477b9a5cdd651d28603"
    )


def test_gnosis_goerli_safe_tx():
    tx_def = create_safe_tx_def(
        version="1.3.0",
        contract_address=GOERLI_MSIG_ADDRESS,
        chain_id=5,
    )

    # Fields matching actual nonce=0 tx from wallet.
    receiver = "0x3c59eC3912A6A0c8690ec548D87FB55C3Ba62aBa"
    msg = tx_def(
        to=receiver,
        nonce=0,
        value=1_000_000_000_000_000_000,
    )
    actual = calculate_hash(msg.signable_message)
    expected = HexBytes("0xbbb1cbed7c3679b5d5764df26af8fab1b15f3a15c084db9082dffb3624ca74ee")
    assert actual == expected
