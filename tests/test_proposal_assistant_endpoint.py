from unittest.mock import patch

import httpx


def _provider_error(status_code, headers=None):
    request = httpx.Request("POST", "https://x")
    return httpx.HTTPStatusError(
        "boom",
        request=request,
        response=httpx.Response(status_code, headers=headers or {}, request=request),
    )


def test_proposal_assistant_endpoint_returns_reply(client, auth_headers):
    body = {
        "messages": [{"role": "user", "content": "Quero criar uma proposta"}],
        "current_draft": None,
        "current_proposal_id": None,
    }
    with patch(
        "app.modules.ai.service.call_ai_provider_with_tools",
        return_value={"content": "Beleza, qual o cliente?", "tool_calls": []},
    ):
        r = client.post("/api/v1/ai/proposal-assistant", json=body, headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["reply"] == "Beleza, qual o cliente?"
    assert data["tool_result"] is None


def test_proposal_assistant_endpoint_requires_auth(client):
    r = client.post("/api/v1/ai/proposal-assistant", json={"messages": []})
    assert r.status_code == 401


def test_proposal_assistant_endpoint_validates_body(client, auth_headers):
    r = client.post("/api/v1/ai/proposal-assistant", json={"foo": "bar"}, headers=auth_headers)
    assert r.status_code == 422


def test_proposal_assistant_endpoint_propagates_provider_5xx(client, auth_headers):
    body = {"messages": [{"role": "user", "content": "x"}]}
    err = _provider_error(503)
    with patch("app.modules.ai.service.call_ai_provider_with_tools", side_effect=err):
        r = client.post("/api/v1/ai/proposal-assistant", json=body, headers=auth_headers)
    assert r.status_code == 504
    assert r.json().get("detail") == "provider_unavailable"


def test_proposal_assistant_endpoint_handles_malformed_retry_after(client, auth_headers):
    body = {"messages": [{"role": "user", "content": "x"}]}
    err = _provider_error(429, headers={"retry-after": "next Tuesday"})
    with patch("app.modules.ai.service.call_ai_provider_with_tools", side_effect=err):
        r = client.post("/api/v1/ai/proposal-assistant", json=body, headers=auth_headers)
    assert r.status_code == 429
    assert r.json()["detail"] == {"detail": "rate_limited", "retry_after_s": None}


def test_proposal_assistant_endpoint_handles_date_retry_after(client, auth_headers):
    body = {"messages": [{"role": "user", "content": "x"}]}
    err = _provider_error(
        429,
        headers={"retry-after": "Wed, 21 Oct 2015 07:28:00 GMT"},
    )
    with patch("app.modules.ai.service.call_ai_provider_with_tools", side_effect=err):
        r = client.post("/api/v1/ai/proposal-assistant", json=body, headers=auth_headers)
    assert r.status_code == 429
    assert r.json()["detail"] == {"detail": "rate_limited", "retry_after_s": None}


def test_proposal_assistant_endpoint_maps_provider_401_to_provider_error(client, auth_headers):
    body = {"messages": [{"role": "user", "content": "x"}]}
    err = _provider_error(401)
    with patch("app.modules.ai.service.call_ai_provider_with_tools", side_effect=err):
        r = client.post("/api/v1/ai/proposal-assistant", json=body, headers=auth_headers)
    assert r.status_code == 502
    assert r.json().get("detail") == "provider_error"
