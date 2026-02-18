"""
PII Redactor - Utilities for masking personally identifiable information.

Examples:
- j.doe@company.com -> j***@***.com
- Jean Dupont -> J*** D***
- 06 12 34 56 78 -> ** ** ** ** **
- 1990-01-15 -> ****-**-**
"""
import re
from typing import Optional


def redact_email(email: str) -> str:
    """Redact email: keep first char and domain TLD."""
    if not email or "@" not in email:
        return email
    local, domain = email.split("@", 1)
    parts = domain.split(".")
    tld = parts[-1] if parts else ""
    return f"{local[0]}***@***.{tld}"


def redact_name(name: str) -> str:
    """Redact name: keep first char of each word."""
    if not name:
        return name
    parts = name.strip().split()
    return " ".join(f"{p[0]}***" if len(p) > 1 else p for p in parts)


def redact_phone(phone: str) -> str:
    """Redact phone number: replace all digits with *."""
    if not phone:
        return phone
    return re.sub(r"\d", "*", phone)


def redact_date(date_str: str) -> str:
    """Redact date: replace with ****-**-**."""
    if not date_str:
        return date_str
    # Handle various date formats
    if re.match(r"\d{4}-\d{2}-\d{2}", date_str):
        return "****-**-**"
    if re.match(r"\d{2}/\d{2}/\d{4}", date_str):
        return "**/**/****"
    return re.sub(r"\d", "*", date_str)


def redact_ssn(ssn: str) -> str:
    """Redact SSN/social security number."""
    if not ssn:
        return ssn
    return re.sub(r"\d", "*", ssn)


def redact_credit_card(cc: str) -> str:
    """Redact credit card: keep last 4 digits."""
    if not cc:
        return cc
    digits = re.sub(r"\D", "", cc)
    if len(digits) < 4:
        return re.sub(r"\d", "*", cc)
    last4 = digits[-4:]
    return re.sub(r"\d(?=\d{4})", "*", cc.rstrip())  # Simple approach
    # Better: mask all but last 4
    masked = "*" * (len(digits) - 4) + last4
    return masked


def redact_address(address: Optional[dict]) -> Optional[dict]:
    """Redact address fields in a JSON address object."""
    if not address or not isinstance(address, dict):
        return address
    redacted = {}
    for key, value in address.items():
        if isinstance(value, str):
            if key in ("street", "line1", "line2", "address_line"):
                # Keep only first word
                parts = value.split()
                redacted[key] = f"{parts[0]} ***" if parts else "***"
            elif key in ("zip", "postal_code", "zip_code"):
                redacted[key] = re.sub(r"\d", "*", value)
            else:
                redacted[key] = value  # Keep city, country, state
        else:
            redacted[key] = value
    return redacted


def redact_text_pii(text: str) -> str:
    """
    Redact common PII patterns in free text.
    Applied to OCR text and agent reasoning.
    """
    if not text:
        return text

    result = text

    # Email addresses
    result = re.sub(
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        lambda m: redact_email(m.group()),
        result,
    )

    # French phone numbers (06, 07, 01-05, +33)
    result = re.sub(
        r"(?:\+33|0)\s*[1-9](?:[\s.-]*\d{2}){4}",
        lambda m: redact_phone(m.group()),
        result,
    )

    # Dates (YYYY-MM-DD, DD/MM/YYYY)
    result = re.sub(
        r"\b\d{4}-\d{2}-\d{2}\b",
        "****-**-**",
        result,
    )
    result = re.sub(
        r"\b\d{2}/\d{2}/\d{4}\b",
        "**/**/****",
        result,
    )

    # French SSN (NIR) - 13 digits + 2 digit key
    result = re.sub(
        r"\b[12]\s*\d{2}\s*\d{2}\s*\d{2}\s*\d{3}\s*\d{3}\s*\d{2}\b",
        lambda m: redact_ssn(m.group()),
        result,
    )

    return result
