"""
Functions for validating EIP-712 message structure (required fields, etc.).
"""

# copied under the MIT license from the eth-account project:
# https://github.com/ethereum/eth-account/blob/41f56e45b49ec1966a72cba12955bc1185cf7284/eth_account/_utils/structured_data/validation.py
# flake8: noqa

import re

from eth_utils import ValidationError

# Regexes
IDENTIFIER_REGEX = r"^[a-zA-Z_$][a-zA-Z_$0-9]*$"
TYPE_REGEX = r"^[a-zA-Z_$][a-zA-Z_$0-9]*(\[([1-9]\d*)*\])*$"


def validate_has_attribute(attr_name, dict_data):
    """
    Validates whether ``dict_data`` contains ``attr_name``, raising
    :class:`eth_utils.ValidationError` if it does not.
    """
    if attr_name not in dict_data:
        raise ValidationError("Attribute `{0}` not found in the JSON string".format(attr_name))


def validate_types_attribute(structured_data):
    """
    Validates the existence of the ``types`` field, its contents, and whether identifer and type
    names are valid. Raises :class:`eth_utils.ValidationError` otherwise.
    """
    # Check that the data has `types` attribute
    validate_has_attribute("types", structured_data)

    # Check if all the `name` and the `type` attributes in each field of all the
    # `types` attribute are valid (Regex Check)
    for struct_name in structured_data["types"]:
        # Check that `struct_name` is of the type string
        if not isinstance(struct_name, str):
            raise ValidationError(
                "Struct Name of `types` attribute should be a string, but got type `{0}`".format(
                    type(struct_name)
                )
            )
        for field in structured_data["types"][struct_name]:
            # Check that `field["name"]` is of the type string
            if not isinstance(field["name"], str):
                raise ValidationError(
                    "Field Name `{0}` of struct `{1}` should be a string, but got type `{2}`".format(
                        field["name"], struct_name, type(field["name"])
                    )
                )
            # Check that `field["type"]` is of the type string
            if not isinstance(field["type"], str):
                raise ValidationError(
                    "Field Type `{0}` of struct `{1}` should be a string, but got type `{2}`".format(
                        field["type"], struct_name, type(field["type"])
                    )
                )
            # Check that field["name"] matches with IDENTIFIER_REGEX
            if not re.match(IDENTIFIER_REGEX, field["name"]):
                raise ValidationError(
                    "Invalid Identifier `{0}` in `{1}`".format(field["name"], struct_name)
                )
            # Check that field["type"] matches with TYPE_REGEX
            if not re.match(TYPE_REGEX, field["type"]):
                raise ValidationError(
                    "Invalid Type `{0}` in `{1}`".format(field["type"], struct_name)
                )


def validate_field_declared_only_once_in_struct(field_name, struct_data, struct_name):
    """
    Validates that the given ``field_name`` only appears once in
    ``struct_data``. Raises :class:`eth_utils.ValidationError` otherwise.
    """
    if len([field for field in struct_data if field["name"] == field_name]) != 1:
        raise ValidationError(
            "Attribute `{0}` not declared or declared more than once in {1}".format(
                field_name, struct_name
            )
        )


EIP712_DOMAIN_FIELDS = [
    "name",
    "version",
    "chainId",
    "verifyingContract",
]


def used_header_fields(EIP712Domain_data):
    """Returns only the ``EIP712_DOMAIN_FIELDS`` from the given domain data."""
    return [field["name"] for field in EIP712Domain_data if field["name"] in EIP712_DOMAIN_FIELDS]


def validate_EIP712Domain_schema(structured_data):
    """
    Verifies that the given ``structured_data`` contains a valid EIP-712
    domain schema. Raises :class:`eth_utils.ValidationError` otherwise.
    """
    # Check that the `types` attribute contains `EIP712Domain` schema declaration
    if "EIP712Domain" not in structured_data["types"]:
        raise ValidationError("`EIP712Domain struct` not found in types attribute")
    # Check that the names and types in `EIP712Domain` are what are mentioned in the EIP-712
    # and they are declared only once (if defined at all)
    EIP712Domain_data = structured_data["types"]["EIP712Domain"]
    header_fields = used_header_fields(EIP712Domain_data)
    if len(header_fields) == 0:
        raise ValidationError(f"One of {EIP712_DOMAIN_FIELDS} must be defined in {structured_data}")
    for field in header_fields:
        validate_field_declared_only_once_in_struct(field, EIP712Domain_data, "EIP712Domain")


def validate_primaryType_attribute(structured_data):
    """
    Verifies that the given ``structured_data`` contains a valid ``primaryType``
    definition. Raises :class:`eth_utils.ValidationError` otherwise.
    """
    # Check that `primaryType` attribute is present
    if "primaryType" not in structured_data:
        raise ValidationError("The Structured Data needs to have a `primaryType` attribute")
    # Check that `primaryType` value is a string
    if not isinstance(structured_data["primaryType"], str):
        raise ValidationError(
            "Value of attribute `primaryType` should be `string`, but got type `{0}`".format(
                type(structured_data["primaryType"])
            )
        )
    # Check that the value of `primaryType` is present in the `types` attribute
    if not structured_data["primaryType"] in structured_data["types"]:
        raise ValidationError(
            "The Primary Type `{0}` is not present in the `types` attribute".format(
                structured_data["primaryType"]
            )
        )


def validate_structured_data(structured_data):
    """
    Top-level validator that verifies ``structured_data`` is a valid according
    to the EIP-712 spec. Raises :class:`eth_utils.ValidationError` otherwise.
    """
    # validate the `types` attribute
    validate_types_attribute(structured_data)
    # validate the `EIP712Domain` struct of `types` attribute
    validate_EIP712Domain_schema(structured_data)
    # validate the `primaryType` attribute
    validate_primaryType_attribute(structured_data)
    # Check that there is a `domain` attribute in the structured data
    validate_has_attribute("domain", structured_data)
    # Check that there is a `message` attribute in the structured data
    validate_has_attribute("message", structured_data)
