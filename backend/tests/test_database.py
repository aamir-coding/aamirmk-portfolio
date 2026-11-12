import asyncio
import io
import json
import os
from collections.abc import AsyncIterator
from pathlib import Path
from threading import Event
from urllib.parse import parse_qs, urlsplit
from uuid import UUID, uuid4

import asyncpg
import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import select

from app.db.models import HandoffRecord, MessageRecord, RecruiterSession
from app.db.session import create_database_engine
from app.fit.models import FitRequest
from app.llm import FakeLLM, get_llm_client
from app.main import create_app
from app.retrieval.models import FactChunk
from app.retrieval.retriever import FakeRetriever, get_retriever
from app.settings import Settings

ALEMBIC_INI = Path(__file__).resolve().parents[1] / "alembic.ini"
TABLES = (
    "sessions",
    "messages",
    "feedback",
    "fit_runs",
    "handoffs",
    "summaries",
    "quota_usage",
)


def test_offline_migration_creates_private_tables_without_credentials() -> None:
    output = io.StringIO()
    config = Config(str(ALEMBIC_INI), output_buffer=output)
    command.upgrade(config, "head", sql=True)
    sql = output.getvalue()
    assert "CREATE SCHEMA portfolio" in sql
    for table in TABLES:
        assert f"CREATE TABLE portfolio.{table}" in sql
    assert "ON DELETE CASCADE" in sql
    assert "UNIQUE (token_hash)" in sql


def test_database_settings_are_optional_and_redacted() -> None:
    assert not Settings(_env_file=None).DATABASE_URL.get_secret_value()
    settings = Settings(
        _env_file=None,
        DATABASE_URL="postgresql://app:database-password@localhost/portfolio",
        ANALYTICS_IP_HASH_KEY="analytics-secret-" * 3,
    )
    assert "database-password" not in repr(settings)
    assert "analytics-secret" not in repr(settings)


def test_chat_remains_available_after_analytics_connection_failure(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    async def unavailable(**_: object) -> None:
        raise ConnectionError("database-private-error")

    monkeypatch.setattr(asyncpg, "connect", unavailable)
    settings = Settings(
        _env_file=None,
        ENVIRONMENT="test",
        DATABASE_URL="postgresql://app:synthetic-password@localhost/portfolio",
        ANALYTICS_IP_HASH_KEY="a" * 43,
    )
    app = create_app(settings)
    app.dependency_overrides[get_llm_client] = lambda: FakeLLM()
    app.dependency_overrides[get_retriever] = lambda: FakeRetriever()
    with TestClient(app) as client:
        assert client.post(
            "/api/chat", json={"message": "Synthetic question"}
        ).is_success
    assert "Analytics write unavailable: ConnectionError" in caplog.text
    assert "database-private-error" not in caplog.text
    assert "Synthetic question" not in caplog.text


@pytest.fixture
def postgres_url(monkeypatch: pytest.MonkeyPatch) -> str:
    url = os.getenv("PORTFOLIO_TEST_DATABASE_URL")
    if not url:
        pytest.skip(
            "Set PORTFOLIO_TEST_DATABASE_URL to a disposable PostgreSQL database"
        )
    parsed = urlsplit(url)
    if (
        parsed.hostname not in {"localhost", "127.0.0.1", "::1"}
        or parsed.path != "/portfolio_test"
        or set(parse_qs(parsed.query)) - {"sslmode"}
    ):
        pytest.fail("Use a disposable loopback portfolio_test database")
    monkeypatch.setenv("MIGRATION_DATABASE_URL", url)
    return url


def test_postgres_migration_round_trip(postgres_url: str) -> None:
    config = Config(str(ALEMBIC_INI))
    command.upgrade(config, "head")
    command.check(config)
    command.downgrade(config, "base")
    command.upgrade(config, "head")
    command.check(config)


def test_analytics_records_resolved_company_and_questions_off_response_path(
    postgres_url: str,
) -> None:
    command.upgrade(Config(str(ALEMBIC_INI)), "head")
    settings = Settings(
        _env_file=None,
        ENVIRONMENT="test",
        DATABASE_URL=postgres_url,
        ANALYTICS_IP_HASH_KEY="a" * 43,
    )
    app = create_app(settings)
    app.dependency_overrides[get_llm_client] = lambda: FakeLLM()
    app.dependency_overrides[get_retriever] = lambda: FakeRetriever()
    headers = {"X-Session-ID": "phase9-disposable-tab", "User-Agent": "Mobile"}
    params = {"for": "ecolab-5a2b"}
    question = "How does the judge queue work?"
    with TestClient(app, client=("192.0.2.18", 5080)) as client:
        assert client.get("/api/context", params=params, headers=headers).is_success
        response = client.post(
            "/api/chat", params=params, headers=headers, json={"message": question}
        )
        assert response.is_success
        known_usage = response.json()["telemetry"]
        response = client.post(
            "/api/chat/stream",
            params=params,
            headers=headers,
            json={"message": question},
        )
        assert response.is_success
        done = response.text.split("event: done\ndata: ", 1)[1].splitlines()[0]
        unknown_usage = json.loads(done)["telemetry"]
        assert known_usage["usage_complete"] is True
        assert unknown_usage["usage_complete"] is False

    async def verify_rows() -> None:
        engine = create_database_engine(SecretStr(postgres_url), pooled=False)
        try:
            async with engine.connect() as connection:
                sessions = (await connection.execute(select(RecruiterSession))).all()
                assert len(sessions) == 1
                session = sessions[0]
                assert session.company_slug == "ecolab-5a2b"
                assert session.device_class == "mobile"
                assert session.opened_at is not None
                assert len(session.ip_hash) == 64
                assert "192.0.2.18" not in session.ip_hash
                messages = (
                    await connection.execute(
                        select(MessageRecord).order_by(MessageRecord.created_at)
                    )
                ).all()
                assert [message.question for message in messages] == [
                    question,
                    question,
                ]
                assert [(row.input_tokens, row.output_tokens) for row in messages] == [
                    (usage["input_tokens"], usage["output_tokens"])
                    for usage in (known_usage, unknown_usage)
                ]
        finally:
            await engine.dispose()

    try:
        asyncio.run(verify_rows())
    finally:
        command.downgrade(Config(str(ALEMBIC_INI)), "base")


def test_handoff_returns_before_delivery_and_recovers_pending_row(
    postgres_url: str,
) -> None:
    class BlockedTelegram:
        def __init__(self) -> None:
            self.started = Event()

        async def send(self, row: HandoffRecord) -> None:
            self.started.set()
            await asyncio.Event().wait()

    class FakeTelegram:
        def __init__(self) -> None:
            self.delivered: list[UUID] = []

        async def send(self, row: HandoffRecord) -> None:
            if row.transcript[0]["content"] == "Simulate delivery failure":
                raise ConnectionError("Synthetic Telegram failure")
            self.delivered.append(row.id)

    async def wait_for_status(id: UUID, status: str) -> None:
        engine = create_database_engine(SecretStr(postgres_url), pooled=False)
        try:
            async with engine.connect() as connection, asyncio.timeout(5):
                while True:
                    actual = await connection.scalar(
                        select(HandoffRecord.delivery_status).where(
                            HandoffRecord.id == id
                        )
                    )
                    if actual == status:
                        return
                    await asyncio.sleep(0.025)
        finally:
            await engine.dispose()

    def payload(id: UUID, text: str) -> dict[str, object]:
        return {
            "id": str(id),
            "consent": True,
            "transcript": [{"role": "user", "content": text}],
        }

    config = Config(str(ALEMBIC_INI))
    command.upgrade(config, "head")
    settings = Settings(_env_file=None, ENVIRONMENT="test", DATABASE_URL=postgres_url)
    first = uuid4()
    second = uuid4()
    blocked = BlockedTelegram()
    try:
        with TestClient(create_app(settings, handoff_notifier=blocked)) as client:
            submission = payload(first, "A real question in a synthetic transcript")
            assert client.post("/api/handoff", json=submission).status_code == 202
            assert blocked.started.wait(timeout=5)
            asyncio.run(wait_for_status(first, "pending"))
            assert client.post("/api/handoff", json=submission).status_code == 202
            conflict = client.post("/api/handoff", json=payload(first, "Changed"))
            assert conflict.status_code == 409

        notifier = FakeTelegram()
        with TestClient(create_app(settings, handoff_notifier=notifier)) as client:
            asyncio.run(wait_for_status(first, "sent"))
            failed = client.post(
                "/api/handoff", json=payload(second, "Simulate delivery failure")
            )
            assert failed.status_code == 202
            asyncio.run(wait_for_status(second, "failed"))
        assert notifier.delivered == [first]
    finally:
        command.downgrade(config, "base")


def test_feedback_and_admin_use_saved_recruiter_activity(postgres_url: str) -> None:
    class FakeTelegram:
        async def send(self, row: HandoffRecord) -> None:
            pass

    class FakeFitPipeline:
        async def run(self, request: FitRequest) -> AsyncIterator[dict[str, object]]:
            yield {
                "event": "complete",
                "data": {
                    "telemetry": {
                        "total_ms": 100,
                        "usage_complete": True,
                        "input_tokens": 7,
                        "output_tokens": 3,
                    }
                },
            }

    config = Config(str(ALEMBIC_INI))
    command.upgrade(config, "head")
    token = "a" * 43
    settings = Settings(
        _env_file=None,
        ENVIRONMENT="test",
        DATABASE_URL=postgres_url,
        ADMIN_TOKEN=token,
        ANALYTICS_IP_HASH_KEY="b" * 43,
        CORS_ORIGINS=["https://portfolio.test"],
    )
    app = create_app(settings, handoff_notifier=FakeTelegram())
    app.state.fit_pipeline_override = FakeFitPipeline()
    app.dependency_overrides[get_llm_client] = lambda: FakeLLM()
    app.dependency_overrides[get_retriever] = lambda: FakeRetriever()
    company = {"for": "ecolab-5a2b"}
    headers = {"X-Session-ID": "recruiter-tab"}
    try:
        with TestClient(app) as client:
            assert client.get(
                "/api/context", params=company, headers=headers
            ).is_success
            question = "What is Aamir's unavailable internal policy?"
            answer = client.post(
                "/api/chat", params=company, headers=headers, json={"message": question}
            )
            assert answer.is_success and answer.json()["handoff"] is True
            answer_id = answer.json()["feedback_id"]
            vote = {
                "answer_id": answer_id,
                "rating": "down",
                "reason": "Needs a source",
            }
            assert client.post("/api/feedback", json=vote, headers=headers).json() == {
                "rating": "down"
            }
            assert client.post(
                "/api/feedback", json=vote | {"rating": "up"}, headers=headers
            ).json() == {"rating": "down"}
            assert (
                client.post(
                    "/api/feedback",
                    json=vote | {"answer_id": str(uuid4())},
                    headers=headers,
                ).status_code
                == 404
            )

            fact = FactChunk(
                id="example", type="project", title="Example", content="Example fact"
            )
            app.dependency_overrides[get_retriever] = lambda: FakeRetriever(
                default_facts=[fact]
            )
            streamed = client.post(
                "/api/chat/stream",
                params=company,
                headers=headers,
                json={"message": "A supported project question"},
            )
            assert streamed.is_success
            done = json.loads(
                streamed.text.split("event: done\ndata: ")[-1].splitlines()[0]
            )
            assert client.post(
                "/api/feedback",
                json={"answer_id": done["feedback_id"], "rating": "up"},
                headers=headers,
            ).is_success
            assert client.post(
                "/api/fit",
                headers=headers,
                json={"jd_text": "PRIVATE-JD " + "Python API development. " * 5},
            ).is_success
            handoff = {
                "id": str(uuid4()),
                "consent": True,
                "transcript": [{"role": "user", "content": question}],
            }
            assert client.post("/api/handoff", json=handoff).status_code == 202

            admin_headers = {
                "Authorization": f"Bearer {token}",
                "Origin": "https://portfolio.test",
            }
            for _ in range(50):
                admin = client.get("/api/admin/dashboard", headers=admin_headers)
                assert admin.is_success
                data = admin.json()
                if data["fit_reports"] == 1:
                    break
                Event().wait(0.025)
            assert admin.headers["Cache-Control"] == "no-store"
            assert (
                admin.headers["Access-Control-Allow-Origin"] == "https://portfolio.test"
            )
            assert "PRIVATE-JD" not in admin.text
            assert data["question_count"] == data["classified_questions"] == 2
            assert data["unanswered_count"] == data["candidate_count"] == 1
            assert data["unanswered"][0]["question"] == question
            assert data["candidates"][0]["reason"] == "Needs a source"
            assert {row["rating"] for row in data["feedback"]} == {"up", "down"}
            assert data["company_opens"] == [{"slug": "ecolab-5a2b", "count": 1}]
            assert {row["count"] for row in data["top_questions"]} == {1}
            assert data["average_latency_ms"] >= 0
            assert data["handoff_count"] == data["fit_reports"] == 1
            assert data["handoffs"][0]["question"] == question
            assert sum(day["known_tokens"] for day in data["usage"]) == 10
            assert sum(day["unknown_runs"] for day in data["usage"]) == 1
    finally:
        command.downgrade(config, "base")
