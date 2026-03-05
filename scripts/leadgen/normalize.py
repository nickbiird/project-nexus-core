"""
Data normalization and cleaning functions for raw lead data.
"""

import logging

from scripts.leadgen.models import Vertical

log = logging.getLogger(__name__)


def clean_value(val: str) -> str:
    """Removes weird markdown links and stray quotes.

    Args:
        val (str): The raw string value to clean.

    Returns:
        str: The cleaned string.

    Raises:
        ValueError: If `val` is not a string.

    Example:
        >>> clean_value('"[john@example.com](mailto:john@example.com)"')
        'john@example.com'
    """
    if not isinstance(val, str):
        raise ValueError("Input value must be a string")

    # Fix [email](mailto:email) -> email
    clean_val = val
    if "](" in clean_val:
        clean_val = clean_val.split("](")[0].replace("[", "")
    clean_val = clean_val.strip().strip('"').strip()

    if clean_val != val:
        log.debug("Cleaned '%s' -> '%s'", val, clean_val)
    elif not clean_val and val:
        log.warning("clean_value resulted in empty string for input: '%s'", val)

    return clean_val


def extract_email(parts: list[str]) -> str | None:
    """Extracts a valid business email from a list of CSV row parts.

    Looks for an email structure (@ and .) and ignores freemail providers like gmail.com.

    Args:
        parts (list[str]): List of string parts from a raw CSV row.

    Returns:
        str | None: The cleaned email string if found, else None.

    Raises:
        TypeError: If `parts` is not a list.

    Example:
        >>> extract_email(["John", "john@business.es", "Other Info"])
        'john@business.es'
    """
    if not isinstance(parts, list):
        raise TypeError("Input must be a list of strings")

    for p in parts:
        if "@" in p and "." in p and "gmail.com" not in p.lower():
            return clean_value(p)
    return None


def extract_linkedin(parts: list[str]) -> str | None:
    """Extracts a LinkedIn URL from a list of CSV row parts.

    Args:
        parts (list[str]): List of string parts from a raw CSV row.

    Returns:
        str | None: The cleaned LinkedIn URL if found, else None.

    Raises:
        TypeError: If `parts` is not a list.

    Example:
        >>> extract_linkedin(["John", "https://linkedin.com/in/john", "CEO"])
        'https://linkedin.com/in/john'
    """
    if not isinstance(parts, list):
        raise TypeError("Input must be a list of strings")

    for p in parts:
        if "linkedin.com/in" in p:
            return clean_value(p)
    return None


def classify_vertical(raw_line: str) -> Vertical:
    """Classifies the business vertical based on text keywords in the raw row.

    Args:
        raw_line (str): The full raw string of the CSV row.

    Returns:
        Vertical: The assigned Vertical enum.

    Raises:
        ValueError: If `raw_line` is not a string.

    Example:
        >>> classify_vertical("Acme Building Materials, 10M revenue")
        <Vertical.CONSTRUCTION_MATERIALS: 'Construction Materials'>
    """
    if not isinstance(raw_line, str):
        raise ValueError("Input must be a string")

    lower_line = raw_line.lower()
    if "construction" in lower_line or "building" in lower_line or "material" in lower_line:
        return Vertical.CONSTRUCTION_MATERIALS

    # Keep as Logistics by default as per the original logic,
    # but could return UNKNOWN if there are no matching keywords.
    # We follow exact original behaviour which assumes anything not construction is logistics,
    # or rely on the original script which initialized as Logistics.
    # To match original behaviour:
    return Vertical.LOGISTICS


def sanitize_company_name(name: str) -> str:
    """Sanitizes a company name by removing artifacts.

    Strips leading dashes, whitespace, stray quotes, and common title-bleeds
    like "Directora " that accidentally prepend the company name.

    Args:
        name (str): The raw company name to sanitize.

    Returns:
        str: The sanitized company name.

    Raises:
        ValueError: If `name` is not a string.

    Example:
        >>> sanitize_company_name(' - "Directora Acme Logistics" ')
        'Acme Logistics'
    """
    if not isinstance(name, str):
        raise ValueError("Input must be a string")

    clean_name = name.strip()

    # Strip leading dashes and stray quotes
    while clean_name.startswith("-") or clean_name.startswith('"') or clean_name.endswith('"'):
        clean_name = clean_name.strip('-" ')

    # Remove common title bleed issues
    title_bleeds = [
        "Director General ",
        "Directora ",
        "Director ",
        "Gerente ",
        "CEO ",
        "Owner ",
        "Fundador ",
        "Propietario ",
    ]

    for title in title_bleeds:
        # Case insensitive match at the beginning
        if clean_name.lower().startswith(title.lower()):
            clean_name = clean_name[len(title) :].strip()

    if clean_name != name:
        log.debug("Sanitized company name: '%s' -> '%s'", name, clean_name)

    return clean_name
