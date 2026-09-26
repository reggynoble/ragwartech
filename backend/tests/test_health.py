from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():

    response = client.get("/api/health")

    assert response.status_code == 200

    assert response.json() == {
        "status": "ok",
        "service": "framework-freefe-api",
    }


def test_create_contact():

    response = client.post(
        "/api/contact",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "message": "This is a test message.",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Test User"
    assert data["email"] == "test@example.com"
    assert data["message"] == "This is a test message."
    assert isinstance(data["id"], int)
    assert data["id"] > 0
    assert "created_at" in data


def test_create_contact_requires_name():

    response = client.post(
        "/api/contact",
        json={
            "email": "test@example.com",
            "message": "Missing name.",
        },
    )

    assert response.status_code == 422


def test_create_contact_requires_email():

    response = client.post(
        "/api/contact",
        json={
            "name": "Test User",
            "message": "Missing email.",
        },
    )

    assert response.status_code == 422


def test_create_contact_rejects_invalid_email():

    response = client.post(
        "/api/contact",
        json={
            "name": "Test User",
            "email": "not-an-email",
            "message": "Invalid email.",
        },
    )

    assert response.status_code == 422


def test_chat(monkeypatch):

    monkeypatch.setattr(
        "app.routes.chat_service.chat",
        lambda message: {
            "response": ("Python and FastAPI are used for backend development."),
            "sources": ["skills.md"],
        },
    )

    response = client.post(
        "/api/chat",
        json={"message": ("What tools are used for server-side development?")},
    )

    assert response.status_code == 200

    data = response.json()

    assert data == {
        "response": ("Python and FastAPI are used for backend development."),
        "sources": ["skills.md"],
    }


def test_chat_unknown_question(monkeypatch):

    monkeypatch.setattr(
        "app.routes.chat_service.chat",
        lambda message: {
            "response": (
                "That information is not available in the portfolio knowledge base."
            ),
            "sources": [],
        },
    )

    response = client.post(
        "/api/chat",
        json={"message": "What is the capital of France?"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data == {
        "response": (
            "That information is not available in the portfolio knowledge base."
        ),
        "sources": [],
    }


def test_chat_requires_message():

    response = client.post(
        "/api/chat",
        json={},
    )

    assert response.status_code == 422


def test_chat_rejects_invalid_message_type():

    response = client.post(
        "/api/chat",
        json={"message": 123},
    )

    assert response.status_code == 422


def test_chat_passes_message_to_chat_service(monkeypatch):

    received = {}

    def fake_chat(message):
        received["message"] = message

        return {
            "response": "Test response",
            "sources": [],
        }

    monkeypatch.setattr(
        "app.routes.chat_service.chat",
        fake_chat,
    )

    response = client.post(
        "/api/chat",
        json={
            "message": "Test message",
        },
    )

    assert response.status_code == 200
    assert received["message"] == "Test message"

    assert response.json() == {
        "response": "Test response",
        "sources": [],
    }
