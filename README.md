# Quick Start

Message classes for typed structured data hashing and signing in Ethereum.
See [EIP-712](https://eips.ethereum.org/EIPS/eip-712) for details.

## Dependencies

- [python3](https://www.python.org/downloads) version 3.8 up to 3.12.

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
    _chainId_ = 1
    _name_ = "Ether Mail"
    _verifyingContract_ = "0xCcCCccccCCCCcCCCCCCcCcCccCcCCCcCcccccccC"
    _version_ = "1"

    sender: Person
    receiver: Person
```

# Initialize a Person object as you would normally

person = Person(name="Joe", wallet="0xa27CEF8aF2B6575903b676e5644657FAe96F491F")
