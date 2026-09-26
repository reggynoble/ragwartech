from unittest.mock import MagicMock

from app.application.chat_service import ChatService


def _documents():
    return [
        {
            "source": "skills.md",
            "chunk": 1,
            "content": "Python and FastAPI are used for backend development.",
        }
    ]


def test_chat_service_without_api_key(monkeypatch):
    monkeypatch.setattr(
        "app.application.chat_service.settings.openai_api_key",
        "",
    )

    service = ChatService(retriever=lambda message: _documents())

    assert service.client is None


def test_chat_service_with_openai_api_key(monkeypatch):
    monkeypatch.setattr(
        "app.application.chat_service.settings.openai_api_key",
        "test-key",
    )

    mock_client = MagicMock()

    service = ChatService(
        client=mock_client,
        retriever=lambda message: _documents(),
    )

    assert service.client is mock_client


def test_chat_uses_rag_fallback(monkeypatch):
    monkeypatch.setattr(
        "app.application.chat_service.settings.openai_api_key",
        "",
    )

    service = ChatService(retriever=lambda message: _documents())

    response = service.chat("What is used for backend development?")

    assert "Python" in response["response"]
    assert "FastAPI" in response["response"]
    assert response["sources"] == ["skills.md"]


def test_unknown_question_does_not_call_openai():
    mock_client = MagicMock()

    service = ChatService(
        client=mock_client,
        retriever=lambda message: [],
    )

    response = service.chat("What is the capital of France?")

    assert response["response"] == (
        "That information is not available in the portfolio knowledge base."
    )
    assert response["sources"] == []
    mock_client.responses.create.assert_not_called()


def test_openai_receives_rag_context():
    mock_client = MagicMock()

    mock_response = MagicMock()
    mock_response.output_text = "Python and FastAPI are used for backend development."
    mock_client.responses.create.return_value = mock_response

    service = ChatService(
        client=mock_client,
        retriever=lambda message: _documents(),
    )

    response = service.chat("What is used for backend development?")

    assert response["response"] == (
        "Python and FastAPI are used for backend development."
    )
    assert response["sources"] == ["skills.md"]

    mock_client.responses.create.assert_called_once()

    call_kwargs = mock_client.responses.create.call_args.kwargs

    assert call_kwargs["model"] == "gpt-5.6-luna"
    assert "Python and FastAPI" in call_kwargs["input"]
    assert "skills.md" in call_kwargs["input"]
    assert "What is used for backend development?" in call_kwargs["input"]


def test_openai_failure_uses_fallback():
    mock_client = MagicMock()
    mock_client.responses.create.side_effect = RuntimeError("OpenAI unavailable")

    service = ChatService(
        client=mock_client,
        retriever=lambda message: _documents(),
    )

    response = service.chat("What is used for backend development?")

    assert "AI service is currently unavailable." in response["response"]
    assert "Python" in response["response"]
    assert "FastAPI" in response["response"]
    assert response["sources"] == ["skills.md"]
