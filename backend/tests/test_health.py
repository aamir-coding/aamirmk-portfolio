from fastapi.testclient import TestClient


def test_health_returns_ok(client: TestClient) -> None:
    """GET /api/health returns 200 with ok status and ready flag."""
    response = client.get("/api/health")

    assert response.status_code == 200
    data = response.json()
    assert data == {"status": "ok", "ready": True}


def test_cors_allows_listed_origin(client: TestClient) -> None:
    """Requests from an allowlisted origin receive CORS header."""
    origin = "http://localhost:5173"
    response = client.get(
        "/api/health",
        headers={"Origin": origin},
    )

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == origin


def test_cors_rejects_unlisted_origin(client: TestClient) -> None:
    """Requests from an unlisted origin do not receive Access-Control-Allow-Origin."""
    response = client.get(
        "/api/health",
        headers={"Origin": "https://unauthorized-domain.com"},
    )

    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


def test_request_id_generated_when_missing(client: TestClient) -> None:
    """Every response gets an X-Request-ID header generated if not supplied."""
    response = client.get("/api/health")

    assert response.status_code == 200
    request_id = response.headers.get("X-Request-ID")
    assert request_id is not None
    assert len(request_id) > 0


def test_request_id_preserved_when_supplied(client: TestClient) -> None:
    """An incoming X-Request-ID header is propagated into the response."""
    custom_id = "recruiter-session-12345"
    response = client.get(
        "/api/health",
        headers={"X-Request-ID": custom_id},
    )

    assert response.status_code == 200
    assert response.headers.get("X-Request-ID") == custom_id


def test_cors_preflight_options_request(client: TestClient) -> None:
    """OPTIONS preflight request from allowlisted origin is permitted."""
    origin = "http://localhost:5173"
    response = client.options(
        "/api/health",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == origin
    assert "GET" in response.headers.get("access-control-allow-methods", "")


def test_double_slash_path_normalized(client: TestClient) -> None:
    """Requests with duplicate consecutive slashes are normalized cleanly."""
    response = client.get("http://testserver//api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "ready": True}


def test_404_returns_consistent_json_error(client: TestClient) -> None:
    """Unknown endpoints return formatted JSON error with code and request ID."""
    response = client.get("/api/nonexistent-route")

    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == 404
    assert data["error"]["message"] == "Not Found"
    assert data["error"]["request_id"] is not None
    assert response.headers.get("X-Request-ID") == data["error"]["request_id"]


def test_response_security_headers(client: TestClient) -> None:
    """Every response contains standard HTTP security hardening headers."""
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
