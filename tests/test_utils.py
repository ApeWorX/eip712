import pytest
from eth_abi.registry import registry

from eip712 import EIP712Message
from eip712.utils import build_eip712_type, get_abi_type

from .conftest import ALL_SUPPORTED_TYPES


@pytest.mark.parametrize("field_type", ALL_SUPPORTED_TYPES)
def test_abi_type(field_type):
    assert registry.has_encoder(get_abi_type(field_type))


@pytest.mark.parametrize("field_type", ALL_SUPPORTED_TYPES)
def test_build_modeltype(field_type):
    class Msg(EIP712Message):
        a: field_type

    assert build_eip712_type(Msg) == {
        "Msg": [
            {"name": "a", "type": get_abi_type(field_type)},
        ],
    }
