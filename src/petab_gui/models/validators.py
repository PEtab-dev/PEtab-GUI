"""Validation utilities for PEtab data."""

import math

import numpy as np


def validate_value(value, expected_type):
    """Validate and convert a value to the expected type.

    Args:
        value: The value to validate and convert
        expected_type: The numpy type to convert the value to

    Returns:
        tuple: A tuple containing:
            - The converted value, or None if conversion failed
            - An error message if conversion failed, or None if successful
    """
    try:
        if expected_type == np.object_:
            value = str(value)
        elif expected_type == np.float64:
            value = float(value)
    except ValueError as e:
        return None, str(e)
    return value, None


def is_invalid(value):
    """Check if a value is invalid.

    Args:
        value: The value to check

    Returns:
        bool: True if the value is invalid (None, NaN, or infinity)
    """
    if value is None:  # None values are invalid
        return True
    if isinstance(value, str):  # Strings can always be displayed
        return False
    try:
        return not math.isfinite(value)
    except TypeError:
        return True
