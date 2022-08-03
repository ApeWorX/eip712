# Quick Start

Message classes for typed structured data hashing and signing in Ethereum.
See [EIP-712](https://eips.ethereum.org/EIPS/eip-712) for details.

## Dependencies

* [python3](https://www.python.org/downloads) version 3.7.2 or greater, python3-dev

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
    _chainId_: "uint256" = 1
    _name_: "string" = "Ether Mail"
    _verifyingContract_: "address" = "0xCcCCccccCCCCcCCCCCCcCcCccCcCCCcCcccccccC"
    _version_: "string" = "1"

    sender: Person
    receiver: Person
```
