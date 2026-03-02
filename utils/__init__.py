import re
from typing import Optional

INVALID_PHONE_MESSAGE = "The phone number provided is invalid. Please confirm you have provided a valid phone number."


def normalize_and_validate_phone_number_ke(phone_number: Optional[str]) -> str:
    if not phone_number:
        raise ValueError("Phone number is required.")

    digits = re.sub(r"\D", "", str(phone_number))

    if digits.startswith("254"):
        normalized = digits
    elif digits.startswith("0"):
        normalized = "254" + digits[1:]
    elif digits.startswith("7"):
        normalized = "254" + digits
    else:
        raise ValueError(INVALID_PHONE_MESSAGE)

    is_valid = (
        len(normalized) == 12
        and normalized.isdigit()
        and normalized.startswith("254")
        and normalized[3] in {"7", "1"}
    )

    if not is_valid:
        raise ValueError(INVALID_PHONE_MESSAGE)

    return normalized


def phone_number_is_valid(phone_number: Optional[str]) -> bool:
    try:
        normalize_and_validate_phone_number_ke(phone_number)
        return True
    except ValueError:
        return False
