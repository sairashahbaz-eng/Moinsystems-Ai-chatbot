from datetime import datetime, timezone

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
from app.notifications.email_service import email_service


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
    # Find active server-created session
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

    # Find existing lead
    lead = (
        db.query(LeadSubmission)
        .filter(
            LeadSubmission.session_id == chat_session.id
        )
        .first()
    )

    # Create lead record if it does not exist
    if lead is None:
        lead = LeadSubmission(
            session_id=chat_session.id,
            full_name="",
            email="",
            contact_number="",
            notification_status="pending",
        )

        db.add(lead)
        db.flush()

    # -------------------------
    # Required fields
    # -------------------------

    if request.full_name is not None:
        valid, error = validate_full_name(
            request.full_name
        )

        if not valid:
            raise HTTPException(
                status_code=422,
                detail=error,
            )

        lead.full_name = request.full_name.strip()

    if request.email is not None:
        valid, error = validate_email(
            request.email
        )

        if not valid:
            raise HTTPException(
                status_code=422,
                detail=error,
            )

        lead.email = request.email.strip().lower()

    if request.contact_number is not None:
        valid, error = validate_contact_number(
            request.contact_number
        )

        if not valid:
            raise HTTPException(
                status_code=422,
                detail=error,
            )

        lead.contact_number = (
            request.contact_number.strip()
        )

    # -------------------------
    # Optional fields
    # -------------------------

    if request.company_name is not None:
        lead.company_name = request.company_name.strip()

    if request.project_summary is not None:
        lead.project_summary = (
            request.project_summary.strip()
        )

    if request.service_interest is not None:
        lead.service_interest = (
            request.service_interest.strip()
        )

    if request.timeline is not None:
        lead.timeline = request.timeline.strip()

    if request.budget_range is not None:
        lead.budget_range = (
            request.budget_range.strip()
        )

    if request.source_page is not None:
        lead.source_page = (
            request.source_page.strip()
        )

    if request.conversation_summary is not None:
        lead.conversation_summary = (
            request.conversation_summary.strip()
        )

    # Save lead information first
    db.commit()
    db.refresh(lead)

    # -------------------------
    # Determine lead state
    # -------------------------

    lead_data = {
        "full_name": lead.full_name,
        "email": lead.email,
        "contact_number": lead.contact_number,
    }

    state = get_next_state(lead_data)

    # -------------------------
    # Send notification only
    # when required fields
    # are complete
    # -------------------------

    if state.value == "complete":

        # Prevent duplicate notification
        if lead.notification_status != "sent":

            payload = {
                "full_name": lead.full_name,
                "email": lead.email,
                "contact_number": lead.contact_number,
                "company_name": lead.company_name,
                "service_interest": lead.service_interest,
                "project_summary": lead.project_summary,
                "timeline": lead.timeline,
                "budget_range": lead.budget_range,
                "source_page": lead.source_page,
                "conversation_summary": (
                    lead.conversation_summary
                ),
                "user_question": None,
                "timestamp": datetime.now(
                    timezone.utc
                ).isoformat(),
            }

            # Mark as sending
            lead.notification_status = "sending"
            lead.notification_error = None
            db.commit()

            result = (
                email_service.send_lead_notification(
                    payload
                )
            )

            if result["success"]:

                lead.notification_status = "sent"
                lead.notification_sent_at = (
                    datetime.now(timezone.utc)
                )
                lead.notification_provider_id = (
                    result.get("provider_message_id")
                )
                lead.notification_error = None

                db.commit()

                message = (
                    "Thank you. Your details have been "
                    "captured successfully and our team "
                    "will contact you shortly."
                )

            else:

                lead.notification_status = "failed"
                lead.notification_error = (
                    result.get("error")
                )

                db.commit()

                # IMPORTANT:
                # Never report success when email failed.
                message = (
                    "Your details were saved, but we "
                    "could not notify our team right now. "
                    "Please try again shortly."
                )

        else:
            message = (
                "Your details have already been "
                "submitted successfully."
            )

    else:

        messages = {
            "ask_name": "Please provide your name.",
            "ask_email": "Please provide your email.",
            "ask_phone": (
                "Please provide your contact number."
            ),
        }

        message = messages[state.value]

    return LeadCaptureResponse(
        session_token=request.session_token,
        state=state.value,
        message=message,
    )