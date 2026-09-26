from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from .application.chat_service import chat_service
from .database import get_db
from .models import ContactMessage
from .schemas import (
    ChatRequest,
    ChatResponse,
    ContactCreate,
    ContactResponse,
)

router = APIRouter(prefix="/api")


@router.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))

    return {
        "status": "ok",
        "service": "framework-freefe-api",
    }


@router.post(
    "/contact",
    response_model=ContactResponse,
)
def create_contact(
    payload: ContactCreate,
    db: Session = Depends(get_db),
):

    message = ContactMessage(
        name=payload.name,
        email=payload.email,
        message=payload.message,
    )

    db.add(message)

    db.commit()

    db.refresh(message)

    return message


@router.post(
    "/chat",
    response_model=ChatResponse,
    response_model_exclude_none=True,
)
def chat(
    payload: ChatRequest,
):
    return chat_service.chat(payload.message)
