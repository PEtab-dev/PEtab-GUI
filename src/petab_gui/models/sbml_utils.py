"""SBML and Antimony conversion utilities."""

import logging
import os

import antimony


def _check_antimony_return_code(code):
    """Helper for checking the antimony response code.

    Raises Exception if error in antimony.

    Args:
        code: antimony response code

    Raises:
        Exception: If antimony encountered an error
    """
    if code < 0:
        raise Exception(f"Antimony: {antimony.getLastError()}")


def sbml_to_antimony(sbml):
    """Convert SBML to antimony string.

    Args:
        sbml: SBML string or file path

    Returns:
        str: Antimony representation
    """
    antimony.clearPreviousLoads()
    antimony.freeAll()
    isfile = False
    try:
        isfile = os.path.isfile(sbml)
    except Exception as e:
        logging.warning(f"Error checking if {sbml} is a file: {str(e)}")
        isfile = False
    if isfile:
        code = antimony.loadSBMLFile(sbml)
    else:
        code = antimony.loadSBMLString(str(sbml))
    _check_antimony_return_code(code)
    return antimony.getAntimonyString(None)


def antimony_to_sbml(ant):
    """Convert Antimony to SBML string.

    Args:
        ant: Antimony string or file path

    Returns:
        str: SBML representation
    """
    antimony.clearPreviousLoads()
    antimony.freeAll()
    try:
        isfile = os.path.isfile(ant)
    except ValueError:
        isfile = False
    if isfile:
        code = antimony.loadAntimonyFile(ant)
    else:
        code = antimony.loadAntimonyString(ant)
    _check_antimony_return_code(code)
    mid = antimony.getMainModuleName()
    return antimony.getSBMLString(mid)
