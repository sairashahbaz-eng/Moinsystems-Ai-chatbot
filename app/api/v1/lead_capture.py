from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.models import ChatSession, LeadSubmission
from app.db.session import get_db
from app.leads.state_machine import get_next_state
from app.leads.validation import (
    validate_contact_number,
    validate_email,
    validate_full_name,
)


router = APIRouter(
    prefix="/api/v1/lead-capture",
    tags=["Lead Capture"],
)


class LeadCaptureRequest(BaseModel):
    session_token: str = Field(..., min_length=1)

    full_name: str | None = None
    email: str | None = None
    contact_number: str | None = None

    company_name: str | None = None
    project_summary: str | None = None
    service_interest: str | None = None
    timeline: str | None = None
    budget_range: str | None = None
    source_page: str | None = None
    conversation_summary: str | None = None


class LeadCaptureResponse(BaseModel):
    session_token: str
    state: str
    message: str


@router.post("", response_model=LeadCaptureResponse)
def capture_lead(
    request: LeadCaptureRequest,
    db: Session = Depends(get_db),
):
    chat_session = (
        db.query(ChatSession)
        .filter(
            ChatSession.session_token == request.session_token,
            ChatSession.status == "active",
        )
        .first()
    )

    if chat_session is None:
        raise HTTPException(
            status_code=404,
            detail="Invalid or inactive session.",
        )

    lead = (
        db.query(LeadSubmission)
        .filter(
            LeadSubmission.session_id == chat_session.id
        )
        .first()
    )

    # Create a temporary database record immediately
    # so information survives across multiple requests.
    if lead is None:
        lead = LeadSubmission(
            session_id=chat_session.id,
            full_name="",
            email="",
            contact_number="",
        )
        db.add(lead)
        db.flush()

    # Required fields
    if request.full_name is not None:
        valid, error = validate_full_name(request.full_name)

        if not valid:
            raise HTTPException(status_code=422, detail=error)

        lead.full_name = request.full_name.strip()

    if request.email is not None:
        valid, error = validate_email(request.email)

        if not valid:
            raise HTTPException(status_code=422, detail=error)

        lead.email = request.email.strip().lower()

    if request.contact_number is not None:
        valid, error = validate_contact_number(
            request.contact_number
        )

        if not valid:
            raise HTTPException(status_code=422, detail=error)

        lead.contact_number = request.contact_number.strip()

    # Optional fields
    if request.company_name is not None:
        lead.company_name = request.company_name

    if request.project_summary is not None:
        lead.project_summary = request.project_summary

    if request.service_interest is not None:
        lead.service_interest = request.service_interest

    if request.timeline is not None:
        lead.timeline = request.timeline

    if request.budget_range is not None:
        lead.budget_range = request.budget_range

    if request.source_page is not None:
        lead.source_page = request.source_page

    if request.conversation_summary is not None:
        lead.conversation_summary = request.conversation_summary

    db.commit()

    # Read saved values from database
    lead_data = {
        "full_name": lead.full_name,
        "email": lead.email,
        "contact_number": lead.contact_number,
    }

    state = get_next_state(lead_data)

    messages = {
        "ask_name": "Please provide your name.",
        "ask_email": "Please provide your email.",
        "ask_phone": "Please provide your contact number.",
        "complete": "Thank you. Your details have been captured successfully.",
    }

    return LeadCaptureResponse(
        session_token=request.session_token,
        state=state.value,
        message=messages[state.value],
    )