import uuid
from unittest.mock import patch

import httpx
import pytest

from app.models.lead_qualification import LeadAction, LeadQualificationConfig


def _provider_error(status_code, headers=None):
    request = httpx.Request("POST", "https://x")
    return httpx.HTTPStatusError(
        "boom",
        request=request,
        response=httpx.Response(status_code, headers=headers or {}, request=request),
    )


def _create_config(db, company_id):
    config = LeadQualificationConfig(
        id=uuid.uuid4(),
        company_id=company_id,
        ideal_segments=["Tech", "SaaS"],
        ideal_company_sizes=["11-50", "51-200"],
        ideal_roles=["Founder", "Head of Growth"],
        weight_segment=20,
        weight_company_size=15,
        weight_role=15,
        weight_urgency=20,
        weight_timing=15,
        weight_pain_level=15,
        bronze_max=25,
        silver_max=50,
        gold_max=75,
        bronze_action=LeadAction.nutrir,
        silver_action=LeadAction.revisar_manualmente,
        gold_action=LeadAction.abordar_agora,
        diamond_action=LeadAction.abordar_agora,
    )
    db.add(config)
    db.commit()
    return config


def test_lead_qualification_assistant_endpoint_requires_auth(client):
    r = client.post("/api/v1/ai/lead-qualification-assistant", json={"messages": []})
    assert r.status_code == 401


def test_lead_qualification_assistant_endpoint_returns_reply_without_tool_result(
    client,
    auth_headers,
    db,
    sample_user,
):
    _create_config(db, sample_user.company_id)
    body = {"messages": [{"role": "user", "content": "Tenho um lead para qualificar"}]}
    with patch(
        "app.modules.ai.service.call_ai_provider_with_tools",
        return_value={"content": "Me envie segmento, cargo e urgencia.", "tool_calls": []},
    ):
        r = client.post("/api/v1/ai/lead-qualification-assistant", json=body, headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["reply"] == "Me envie segmento, cargo e urgencia."
    assert data["tool_result"] is None


def test_lead_qualification_assistant_endpoint_propagates_provider_5xx(
    client,
    auth_headers,
    db,
    sample_user,
):
    _create_config(db, sample_user.company_id)
    body = {"messages": [{"role": "user", "content": "x"}]}
    err = _provider_error(503)
    with patch("app.modules.ai.service.call_ai_provider_with_tools", side_effect=err):
        r = client.post("/api/v1/ai/lead-qualification-assistant", json=body, headers=auth_headers)
    assert r.status_code == 504
    assert r.json().get("detail") == "provider_unavailable"


def test_lead_qualification_assistant_endpoint_handles_retry_after(
    client,
    auth_headers,
    db,
    sample_user,
):
    _create_config(db, sample_user.company_id)
    body = {"messages": [{"role": "user", "content": "x"}]}
    err = _provider_error(429, headers={"retry-after": "12"})
    with patch("app.modules.ai.service.call_ai_provider_with_tools", side_effect=err):
        r = client.post("/api/v1/ai/lead-qualification-assistant", json=body, headers=auth_headers)
    assert r.status_code == 429
    assert r.json()["detail"] == {"detail": "rate_limited", "retry_after_s": 12}


@pytest.mark.parametrize("provider_status", [401, 403])
def test_lead_qualification_assistant_endpoint_maps_provider_auth_errors_to_provider_error(
    provider_status,
    client,
    auth_headers,
    db,
    sample_user,
):
    _create_config(db, sample_user.company_id)
    body = {"messages": [{"role": "user", "content": "x"}]}
    err = _provider_error(provider_status)
    with patch("app.modules.ai.service.call_ai_provider_with_tools", side_effect=err):
        r = client.post("/api/v1/ai/lead-qualification-assistant", json=body, headers=auth_headers)
    assert r.status_code == 502
    assert r.json().get("detail") == "provider_error"
