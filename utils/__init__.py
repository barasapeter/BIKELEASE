import re
from typing import Optional
from core.errors import InvalidPhoneNumberException


def format_duration_progressive(total_minutes: int) -> str:
    total_seconds = int(total_minutes or .1 * 60)

    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    if hours > 0:
        return f"{hours}h {minutes}m"
    if minutes > 0:
        return f"{minutes}m"
    return f"{seconds}s"


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
        raise InvalidPhoneNumberException

    is_valid = (
        len(normalized) == 12
        and normalized.isdigit()
        and normalized.startswith("254")
        and normalized[3] in {"7", "1"}
    )

    if not is_valid:
        raise InvalidPhoneNumberException

    return normalized


def phone_number_is_valid(phone_number: Optional[str]) -> bool:
    try:
        normalize_and_validate_phone_number_ke(phone_number)
        return True
    except ValueError:
        return False
