from pathlib import Path

from fastapi.testclient import TestClient

from app.config import settings
from app.main import create_app


def _preflight(origin: str):
    client = TestClient(create_app())
    return client.options(
        "/health",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
        },
    )


def test_health_allows_explicit_origin(monkeypatch):
    monkeypatch.setattr(settings, "cors_origins", "http://localhost:5173")
    monkeypatch.setattr(settings, "cors_origin_regex", "")

    response = _preflight("http://localhost:5173")

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_health_allows_vercel_preview_origin_with_regex(monkeypatch):
    monkeypatch.setattr(settings, "cors_origins", "http://localhost:5173")
    monkeypatch.setattr(settings, "cors_origin_regex", r"https://.*\.vercel\.app")

    preview_origin = "https://seven-tools-front-git-feature-ci-smoke-test.vercel.app"
    response = _preflight(preview_origin)

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == preview_origin


def test_render_blueprint_allows_production_frontend_origin():
    assert "https://seven-tools.vercel.app" in Path("render.yaml").read_text(encoding="utf-8")
