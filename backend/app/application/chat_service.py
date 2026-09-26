"""Application service for portfolio AI chat."""

from __future__ import annotations

from collections.abc import Callable
from time import perf_counter

from openai import APIError, OpenAI

from ..config import settings
from ..observability.latency import LatencyTimer
from ..rag.context import build_context
from ..rag.prompts import RAG_SYSTEM_PROMPT
from ..rag.retriever import retrieve

Retriever = Callable[[str], list[dict]]


class ChatService:
    """Orchestrate retrieval, context construction, and generation."""

    def __init__(
        self,
        *,
        client: OpenAI | None = None,
        retriever: Retriever = retrieve,
    ) -> None:
        self.api_key = settings.openai_api_key
        self.model = settings.ai_model
        self._retriever = retriever

        if client is not None:
            self.client = client
        else:
            self.client = OpenAI(api_key=self.api_key) if self.api_key else None

    def _fallback_response(self, context: str) -> str:
        if not context:
            return "That information is not available in the portfolio knowledge base."

        return (
            "AI service is currently unavailable. "
            "Here is the relevant portfolio information:\n\n"
            f"{context}"
        )

    def chat(self, message: str) -> dict:
        """Process a portfolio AI chat request."""
        timer = LatencyTimer.start()

        retrieval_started = perf_counter()
        documents = self._retriever(message)
        timer.record("retrieval_ms", retrieval_started)

        sources = [document["source"] for document in documents]

        if not documents:
            return {
                "response": (
                    "That information is not available in the portfolio knowledge base."
                ),
                "sources": [],
                "latency": {
                    **timer.stages,
                    "total_ms": timer.total_ms(),
                },
            }

        context_started = perf_counter()
        context = build_context(message, results=documents)
        timer.record("context_ms", context_started)

        if not context:
            return {
                "response": (
                    "That information is not available in the portfolio knowledge base."
                ),
                "sources": [],
                "latency": {
                    **timer.stages,
                    "total_ms": timer.total_ms(),
                },
            }

        if not self.client:
            return {
                "response": self._fallback_response(context),
                "sources": sources,
                "latency": {
                    **timer.stages,
                    "total_ms": timer.total_ms(),
                },
            }

        prompt_started = perf_counter()
        prompt = f"Portfolio context:\n\n{context}\n\nUser question:\n\n{message}"
        timer.record("prompt_ms", prompt_started)

        llm_started = perf_counter()

        try:
            response = self.client.responses.create(
                model=self.model,
                instructions=RAG_SYSTEM_PROMPT,
                input=prompt,
            )
        except (APIError, RuntimeError) as exc:
            timer.record("llm_ms", llm_started)
            print(f"OpenAI API error: {type(exc).__name__}: {exc}")

            return {
                "response": self._fallback_response(context),
                "sources": sources,
                "latency": {
                    **timer.stages,
                    "total_ms": timer.total_ms(),
                },
            }

        timer.record("llm_ms", llm_started)

        return {
            "response": response.output_text,
            "sources": sources,
            "latency": {
                **timer.stages,
                "total_ms": timer.total_ms(),
            },
        }


chat_service = ChatService()
