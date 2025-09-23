"""
Format validators for JSON Schema string formats.

This module provides format validation functions for JSON Schema string formats
like email, date, uri, etc. Format validators can be registered and used by
SchemaString templates.
"""

import re
import ipaddress
from datetime import datetime
from typing import Callable, Dict
from urllib.parse import urlparse


# Registry of format validators
FORMAT_VALIDATORS: Dict[str, Callable[[str], bool]] = {}


def register_format(name: str):
    """
    Decorator to register a format validator function.

    Args:
        name: The format name (e.g., 'email', 'date')

    Returns:
        Decorator function that registers the validator
    """

    def decorator(func: Callable[[str], bool]):
        FORMAT_VALIDATORS[name] = func
        return func

    return decorator


@register_format("email")
def validate_email(value: str) -> bool:
    """
    Validate email format according to a basic regex pattern.

    This is a simple validation that checks for the basic structure:
    - At least one character before @
    - @ symbol
    - At least one character after @
    - A dot
    - At least one character after the dot

    Args:
        value: The string value to validate

    Returns:
        True if the value matches email format, False otherwise
    """
    if not isinstance(value, str):
        return False

    # Basic email pattern - more permissive than RFC 5322 for practicality
    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    return re.match(pattern, value) is not None


@register_format("date")
def validate_date(value: str) -> bool:
    """
    Validate date format according to RFC 3339 (YYYY-MM-DD).

    Args:
        value: The string value to validate

    Returns:
        True if the value matches date format, False otherwise
    """
    if not isinstance(value, str):
        return False

    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False


@register_format("date-time")
def validate_date_time(value: str) -> bool:
    """
    Validate date-time format according to RFC 3339.

    Accepts formats like:
    - 2023-12-25T10:30:00Z
    - 2023-12-25T10:30:00+00:00
    - 2023-12-25T10:30:00.123Z

    Args:
        value: The string value to validate

    Returns:
        True if the value matches date-time format, False otherwise
    """
    if not isinstance(value, str):
        return False

    # Common date-time patterns for RFC 3339
    patterns = [
        r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$",  # 2023-12-25T10:30:00Z
        # with milliseconds
        r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$",
        # with timezone
        r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$",
        # full format with milliseconds and timezone
        r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}[+-]\d{2}:\d{2}$",
    ]

    for pattern in patterns:
        if re.match(pattern, value):
            # Additional validation: parse both date and time parts
            try:
                if "T" not in value:
                    continue

                date_time_parts = value.split("T")
                date_part = date_time_parts[0]
                time_part = date_time_parts[1]

                # Validate date part
                datetime.strptime(date_part, "%Y-%m-%d")

                # Validate time part - remove timezone and milliseconds
                # for parsing
                time_for_validation = time_part
                if time_for_validation.endswith("Z"):
                    time_for_validation = time_for_validation[:-1]
                elif "+" in time_for_validation:
                    time_for_validation = time_for_validation.split("+")[0]
                elif time_for_validation.count("-") > 0:
                    # Handle negative timezone offsets
                    parts = time_for_validation.split("-")
                    if len(parts) > 1 and ":" in parts[-1]:
                        time_for_validation = "-".join(parts[:-1])

                # Handle milliseconds
                if "." in time_for_validation:
                    time_format = "%H:%M:%S.%f"
                else:
                    time_format = "%H:%M:%S"

                datetime.strptime(time_for_validation, time_format)
                return True
            except ValueError:
                continue

    return False


@register_format("uri")
def validate_uri(value: str) -> bool:
    """
    Validate URI format according to RFC 3986.

    Args:
        value: The string value to validate

    Returns:
        True if the value matches URI format, False otherwise
    """
    if not isinstance(value, str):
        return False

    try:
        result = urlparse(value)
        # Must have a scheme and netloc (for absolute URIs)
        return bool(result.scheme and result.netloc)
    except Exception:
        return False


@register_format("uuid")
def validate_uuid(value: str) -> bool:
    """
    Validate UUID format (RFC 4122).

    Accepts formats like: 123e4567-e89b-12d3-a456-426614174000

    Args:
        value: The string value to validate

    Returns:
        True if the value matches UUID format, False otherwise
    """
    if not isinstance(value, str):
        return False

    # UUID pattern: 8-4-4-4-12 hexadecimal digits
    pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    return re.match(pattern, value.lower()) is not None


@register_format("ipv4")
def validate_ipv4(value: str) -> bool:
    """
    Validate IPv4 address format.

    Args:
        value: The string value to validate

    Returns:
        True if the value matches IPv4 format, False otherwise
    """
    if not isinstance(value, str):
        return False

    try:
        ipaddress.IPv4Address(value)
        return True
    except ipaddress.AddressValueError:
        return False


@register_format("ipv6")
def validate_ipv6(value: str) -> bool:
    """
    Validate IPv6 address format.

    Args:
        value: The string value to validate

    Returns:
        True if the value matches IPv6 format, False otherwise
    """
    if not isinstance(value, str):
        return False

    try:
        ipaddress.IPv6Address(value)
        return True
    except ipaddress.AddressValueError:
        return False


def get_format_validator(format_name: str) -> Callable[[str], bool]:
    """
    Get a format validator by name.

    Args:
        format_name: The name of the format (e.g., 'email')

    Returns:
        The validator function, or None if not found
    """
    return FORMAT_VALIDATORS.get(format_name)


def is_format_supported(format_name: str) -> bool:
    """
    Check if a format is supported.

    Args:
        format_name: The name of the format to check

    Returns:
        True if the format is supported, False otherwise
    """
    return format_name in FORMAT_VALIDATORS
