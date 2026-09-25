"""Backward-compatible interface for the portfolio AI service."""

from __future__ import annotations

from .application.chat_service import ChatService
from .config import settings


class AIService(ChatService):
    """Backward-compatible alias for ChatService."""


ai_service = AIService()

__all__ = [
    "AIService",
    "ai_service",
    "settings",
]
