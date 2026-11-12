import pytest
from fastapi.testclient import TestClient


def test_ecolab_context_uses_catalog_projects(client: TestClient) -> None:
    response = client.get("/api/context", params={"for": "ecolab-5a2b"})
    assert response.status_code == 200
    data = response.json()["company"]
    assert data["slug"] == "ecolab-5a2b"
    assert "Ecolab" in data["greeting"]
    assert len(data["suggested_questions"]) == 3
    assert [item["id"] for item in data["highlighted_projects"]] == [
        "entropy-oj",
        "ai-digital-assistant",
    ]
    assert data["why_us"]


@pytest.mark.parametrize("slug", ["", "ecolab", "<script>marker</script>", "a" * 200])
def test_unknown_context_is_default(client: TestClient, slug: str) -> None:
    response = client.get("/api/context", params={"for": slug})
    assert response.status_code == 200
    assert response.json() == client.get("/api/context").json() == {"company": None}
