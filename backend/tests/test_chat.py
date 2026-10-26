"""Tests for POST /api/chat endpoint using FakeLLM dependency override."""

from collections.abc import Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.llm import (
    FakeLLM,
    LLMAuthError,
    LLMRateLimitError,
    LLMUnavailableError,
    Message,
    get_llm_client,
)
from app.main import create_app
from app.prompt_loader import SYSTEM_PROMPT
from app.settings import Settings


@pytest.fixture
def fake_llm() -> FakeLLM:
    return FakeLLM(
        reply="Aamir has built full-stack and LLM applications.",
        model="fake-gpt-120b",
    )


@pytest.fixture
def chat_client(
    test_settings: Settings, fake_llm: FakeLLM
) -> Generator[tuple[TestClient, FakeLLM]]:
    app: FastAPI = create_app(settings=test_settings)
    app.dependency_overrides[get_llm_client] = lambda: fake_llm
    with TestClient(app, base_url="http://testserver") as test_client:
        yield test_client, fake_llm
    app.dependency_overrides.clear()


def test_chat_success(chat_client: tuple[TestClient, FakeLLM]) -> None:
    client, fake = chat_client
    response = client.post(
        "/api/chat",
        json={"message": "What is Aamir's experience?"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["reply"] == "Aamir has built full-stack and LLM applications."
    assert data["model"] == "fake-gpt-120b"
    assert data["conversation_id"] is not None
    assert data["usage"]["total_tokens"] == 15

    # Verify FakeLLM received correct messages
    assert len(fake.last_messages) == 2
    assert fake.last_messages[0].role == "system"
    assert fake.last_messages[0].content == SYSTEM_PROMPT
    assert fake.last_messages[1].role == "user"
    assert fake.last_messages[1].content == "What is Aamir's experience?"


def test_chat_preserves_conversation_id(
    chat_client: tuple[TestClient, FakeLLM],
) -> None:
    client, _ = chat_client
    response = client.post(
        "/api/chat",
        json={
            "message": "Tell me about his projects",
            "conversation_id": "recruiter-session-42",
        },
    )

    assert response.status_code == 200
    assert response.json()["conversation_id"] == "recruiter-session-42"


def test_chat_generates_conversation_id_when_omitted(
    chat_client: tuple[TestClient, FakeLLM],
) -> None:
    client, _ = chat_client
    response = client.post("/api/chat", json={"message": "Hello"})

    assert response.status_code == 200
    conv_id = response.json()["conversation_id"]
    assert conv_id
    assert len(conv_id) >= 16


def test_chat_rejects_empty_message(
    chat_client: tuple[TestClient, FakeLLM],
) -> None:
    client, _ = chat_client
    response = client.post("/api/chat", json={"message": "   "})

    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == 422
    assert "Validation error" in data["error"]["message"]


def test_chat_propagates_request_id(
    chat_client: tuple[TestClient, FakeLLM],
) -> None:
    client, _ = chat_client
    headers = {"X-Request-ID": "test-req-trace-001"}
    response = client.post(
        "/api/chat",
        json={"message": "Hello"},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.headers.get("X-Request-ID") == "test-req-trace-001"


def test_chat_handles_rate_limit(test_settings: Settings) -> None:
    class RateLimitedLLM:
        async def complete(self, messages: list[Message]) -> None:
            raise LLMRateLimitError("TPM exceeded")

    app = create_app(settings=test_settings)
    app.dependency_overrides[get_llm_client] = lambda: RateLimitedLLM()

    with TestClient(app, base_url="http://testserver") as client:
        response = client.post("/api/chat", json={"message": "Hi"})
        assert response.status_code == 429
        data = response.json()
        assert data["error"]["code"] == 429
        assert "Rate limit" in data["error"]["message"]


def test_chat_handles_auth_error(test_settings: Settings) -> None:
    class AuthFailingLLM:
        async def complete(self, messages: list[Message]) -> None:
            raise LLMAuthError("Invalid API key")

    app = create_app(settings=test_settings)
    app.dependency_overrides[get_llm_client] = lambda: AuthFailingLLM()

    with TestClient(app, base_url="http://testserver") as client:
        response = client.post("/api/chat", json={"message": "Hi"})
        assert response.status_code == 500
        data = response.json()
        assert data["error"]["code"] == 500
        assert "authentication" in data["error"]["message"].lower()


def test_chat_handles_upstream_unavailable(test_settings: Settings) -> None:
    class UnavailableLLM:
        async def complete(self, messages: list[Message]) -> None:
            raise LLMUnavailableError("503 Service Unavailable")

    app = create_app(settings=test_settings)
    app.dependency_overrides[get_llm_client] = lambda: UnavailableLLM()

    with TestClient(app, base_url="http://testserver") as client:
        response = client.post("/api/chat", json={"message": "Hi"})
        assert response.status_code == 503
        data = response.json()
        assert data["error"]["code"] == 503
        assert "unavailable" in data["error"]["message"].lower()
