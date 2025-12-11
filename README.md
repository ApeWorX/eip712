# Quick Start

Message classes for typed structured data hashing and signing in Ethereum.
See [EIP-712](https://eips.ethereum.org/EIPS/eip-712) for details.

## Dependencies

- [python3](https://www.python.org/downloads) version 3.10 up to 3.14.

## Installation

### via `pip`

You can install the latest release via [`pip`](https://pypi.org/project/pip/):

```bash
pip install eip712
```

### via `uv`

You can clone the repository and use [`uv`](https://docs.astral.sh/uv) for the most up-to-date version:

```bash
git clone https://github.com/ApeWorX/eip712.git
cd eip712
uv sync --group dev
```

## Quick Usage

Define EIP-712 models:

```python
from eip712.messages import EIP712Message

# NOTE: It is **highly** recommended to use ABI types from this library
from eth_pydantic_types import abi

from pydantic import BaseModel


# You can define your inner nested types using normal Pydantic models
class Person(EIP712Type):
    # Define fields using types from the `abi` module
    name: abi.string
    wallet: abi.address


# All valid EIP712 Message Structs **must** subclass `EIP712Message`
class Mail(EIP712Message):
    #  to define your EIP712 domain configuration
    eip712_domain = EIP712Domain(
        name="Ether Mail",
        version="1",
        verifyingContract="0xDDdDddDdDdddDDddDDddDDDDdDdDDdDDdDDDDDDd",
        chainId=1,
    )

    # Struct fields (can be "basic" types, `BaseModel` types, or arrays of either)
    sender: Person
    # Dynamic array support is as easy as using `list` with the corresponding type
    receivers: list[Person]
    ttl: abi.uint256
```

Then initialize these models:

```python
sender = Person(name="Alice", wallet="0xaAaAaAaaAaAaAaaAaAAAAAAAAaaaAaAaAaaAaaAa")
receivers = [
    Person(name="Bob", wallet="0xbBbBBBBbbBBBbbbBbbBbbbbBBbBbbbbBbBbbBBbB"),
    Person(name="Charlie", wallet="0xCcCCccccCCCCcCCCCCCcCcCccCcCCCcCcccccccC"),
]
mail = Mail(sender=sender, receiver=receiver)
```

Finally, you can sign these messages using `eth-account`:

```python
from eth_account import Account

acct = Account.from_key(private_key)
sig = acct.sign_message(mail.signable_message)
```

or natively in [Ape](https://docs.apeworx.io/ape):

```python
# `ape console`
me = accounts.load(me)
sig = me.sign_message(mail)
```
