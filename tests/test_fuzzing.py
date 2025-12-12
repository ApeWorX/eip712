import string as python_string

import pytest
from eth_abi.tools._strategies import get_abi_strategy
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import create_model

from eip712 import EIP712Message
from eip712.messages import EIP712Domain
from eip712.utils import get_abi_type

from .conftest import ALL_SUPPORTED_TYPES


@settings(max_examples=5000)
@pytest.mark.fuzzing
@given(
    types=st.lists(st.sampled_from(ALL_SUPPORTED_TYPES), min_size=1, max_size=10),
    data=st.data(),  # NOTE: This actually seeds the test case
)
def test_random_message_def(types, data):
    members = python_string.ascii_lowercase[: len(types)]
    Msg = create_model("Msg", __base__=EIP712Message, **dict(zip(members, types, strict=True)))
    Msg.eip712_domain = EIP712Domain(name="Doesn't matter")

    values = [data.draw((get_abi_strategy(get_abi_type(t))), label=t) for t in types]
    msg_dict = dict(zip(members, values, strict=True))
    msg = Msg(**msg_dict)

    for k, v in msg_dict.items():
        assert getattr(msg, k) == v
