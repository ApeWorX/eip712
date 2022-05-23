# eip712

Message classes for typed structured data hashing and signing in Ethereum.
See [EIP-712](https://eips.ethereum.org/EIPS/eip-712) for details.

## Dependencies

* [python3](https://www.python.org/downloads) version 3.6 or greater, python3-dev

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

Create EIP-712 models:

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


sender = Person("Cow", "0xCD2a3d9F938E13CD947Ec05AbC7FE734Df8DD826")
receiver = Person("Bob", "0xB0B0b0b0b0b0B000000000000000000000000000")
mail = Mail(sender=TEST_SENDER, receiver=TEST_RECEIVER)

print(f"Do you wish to sign {mail.signable_message}?")
```

## Development

This project is in early development and should be considered an alpha.
Things might not work, breaking changes are likely.
Comments, questions, criticisms and pull requests are welcomed.

## License

This project is licensed under the [Apache 2.0 license](https://github.com/ApeWorX/eip712/blob/main/LICENSE).
