from enum import Enum


class LeadState(str, Enum):
    NOT_STARTED = "not_started"
    ASK_NAME = "ask_name"
    ASK_EMAIL = "ask_email"
    ASK_PHONE = "ask_phone"
    COMPLETE = "complete"


REQUIRED_FIELDS = [
    "full_name",
    "email",
    "contact_number",
]


def next_missing_field(lead_data: dict) -> str | None:
    """
    Return the first required lead field that is still missing.
    """

    for field in REQUIRED_FIELDS:
        value = lead_data.get(field)

        if value is None:
            return field

        if isinstance(value, str) and not value.strip():
            return field

    return None


def get_next_state(lead_data: dict) -> LeadState:
    """
    Determine the backend-controlled lead state.
    """

    missing_field = next_missing_field(lead_data)

    if missing_field == "full_name":
        return LeadState.ASK_NAME

    if missing_field == "email":
        return LeadState.ASK_EMAIL

    if missing_field == "contact_number":
        return LeadState.ASK_PHONE

    return LeadState.COMPLETE