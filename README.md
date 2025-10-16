# Quick Start

Message classes for typed structured data hashing and signing in Ethereum.
See [EIP-712](https://eips.ethereum.org/EIPS/eip-712) for details.

## Dependencies

- [python3](https://www.python.org/downloads) version 3.9 up to 3.12.

## Installation

### via `pip`

You can install the latest release via [`pip`](https://pypi.org/project/pip/):

```bash
pip install eip712
```

### via `setuptools`

You can clone the repository and use [`setuptools`](https://github.com/pypa/setuptools) for the most up-to-date version:

```bash
git clone https://github.com/ApeWorX/eip712.git
cd eip712
python3 setup.py install
```

## Quick Usage

Define EIP-712 models:

```python
from eip712.messages import EIP712Message, EIP712Type


class Person(EIP712Type):
    name: "string"
    wallet: "address"


class Mail(EIP712Message):
    # NOTE: Make sure to define your EIP712 domain configuration
    _chainId_ = 1
    _name_ = "Ether Mail"
    _verifyingContract_ = "0xDDdDddDdDdddDDddDDddDDDDdDdDDdDDdDDDDDDd"
    _version_ = "1"

    # Struct fields (can be "basic" types, `EIP712Type` structs, or arrays of either)
    sender: Person
    receivers: list[Person]
    # NOTE: Define "basic" ABI types as strings
    ttl: "uint256"
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
