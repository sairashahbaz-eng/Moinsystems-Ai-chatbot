import re


PLACEHOLDER_VALUES = {
    "",
    "test",
    "testing",
    "abc",
    "xyz",
    "none",
    "null",
    "n/a",
    "na",
    "unknown",
    "asdf",
    "qwerty",
}


def is_placeholder(value: str) -> bool:
    if not value:
        return True

    normalized = value.strip().lower()

    return normalized in PLACEHOLDER_VALUES


def validate_full_name(value: str) -> tuple[bool, str | None]:
    if is_placeholder(value):
        return False, "Please provide your real full name."

    value = value.strip()

    if len(value) < 2:
        return False, "Full name is too short."

    if len(value) > 255:
        return False, "Full name is too long."

    return True, None


def validate_email(value: str) -> tuple[bool, str | None]:
    if is_placeholder(value):
        return False, "Please provide a valid email address."

    value = value.strip().lower()

    email_pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

    if not re.match(email_pattern, value):
        return False, "Please provide a valid email address."

    if len(value) > 255:
        return False, "Email address is too long."

    return True, None


def validate_contact_number(value: str) -> tuple[bool, str | None]:
    if is_placeholder(value):
        return False, "Please provide a valid contact number."

    value = value.strip()

    digits = re.sub(r"\D", "", value)

    if len(digits) < 7:
        return False, "Please provide a valid contact number."

    if len(digits) > 15:
        return False, "Please provide a valid contact number."

    return True, None