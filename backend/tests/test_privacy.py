"""Sentinel privacy regressions across real request and rewrite paths."""

import logging
import subprocess
import sys
from pathlib import Path
from textwrap import dedent

import httpx
import pytest

from app.llm import FakeLLM, LLMUnavailableError, get_llm_client
from app.main import create_app
from app.models import ChatHistoryMessage
from app.retrieval.retriever import FakeRetriever, get_retriever
from app.retrieval.rewriter import rewrite_follow_up_query
from app.settings import Settings

SENTINEL = "PRIVATE_RECRUITER_SENTINEL"


@pytest.mark.asyncio
async def test_request_logs_exclude_raw_ip_request_ids_and_provider_error_text(
    caplog,
) -> None:
    caplog.set_level(logging.INFO, logger="app")
    app = create_app(Settings(_env_file=None))
    app.dependency_overrides[get_llm_client] = lambda: FakeLLM(
        error_to_raise=LLMUnavailableError(SENTINEL)
    )
    app.dependency_overrides[get_retriever] = lambda: FakeRetriever()
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app, client=("198.51.100.123", 1234)),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/chat", json={"message": SENTINEL}, headers={"x-request-id": SENTINEL}
        )
    assert response.status_code == 503
    assert response.headers["x-request-id"] != SENTINEL
    assert SENTINEL not in caplog.text
    assert "198.51.100.123" not in caplog.text
    assert "ip_hash" in caplog.text


@pytest.mark.asyncio
async def test_rewrite_logs_never_capture_queries_or_generated_text(caplog) -> None:
    caplog.set_level(logging.INFO, logger="app")
    await rewrite_follow_up_query(
        "tell me more",
        [ChatHistoryMessage(role="user", content=SENTINEL)],
        FakeLLM(reply=SENTINEL),
    )
    assert SENTINEL not in caplog.text


def test_production_uvicorn_logs_omit_raw_targets_and_exception_payloads() -> None:
    """Exercise Uvicorn's own handlers in an isolated real HTTP process."""
    source = dedent("""
        import socket
        import threading
        import time
        import httpx
        import uvicorn
        from app.main import create_app
        from app.settings import Settings

        app = create_app(Settings(_env_file=None))
        @app.get('/privacy-fault')
        async def fault():
            raise RuntimeError('PRIVATE_RECRUITER_SENTINEL')
        listener = socket.socket()
        listener.bind(('127.0.0.1', 0))
        listener.listen()
        port = listener.getsockname()[1]
        server = uvicorn.Server(uvicorn.Config(
            app, lifespan='off', log_config='logging.json',
            access_log=False, proxy_headers=False, ws='none'))
        runner = threading.Thread(target=server.run, kwargs={'sockets': [listener]})
        runner.start()
        try:
            deadline = time.monotonic() + 5
            while not server.started:
                assert time.monotonic() < deadline
                time.sleep(.01)
            with httpx.Client() as client:
                response = client.get(
                    f'http://127.0.0.1:{port}/privacy-fault?PRIVATE_RECRUITER_SENTINEL')
            assert response.status_code == 500
        finally:
            server.should_exit = True
            runner.join(timeout=5)
            listener.close()
        assert not runner.is_alive()
    """)
    result = subprocess.run(
        [sys.executable, "-c", source],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, result.stderr
    logs = result.stdout + result.stderr
    assert "RuntimeError" in logs
    assert SENTINEL not in logs
    assert "127.0.0.1" not in logs
