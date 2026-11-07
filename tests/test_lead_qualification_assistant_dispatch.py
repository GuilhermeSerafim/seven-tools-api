import json
import uuid

import pytest
from pydantic import ValidationError

from app.models.lead_qualification import LeadAction, LeadQualificationConfig, QualifiedLead
from app.modules.ai.schemas import (
    LeadQualificationAssistantRequest,
    LeadQualificationLeadExtract,
)
from app.modules.ai.service import lead_qualification_assistant_turn
from app.modules.ai.tools import LEAD_QUALIFICATION_REQUIRED_FIELDS


def _mock_completion(reply="ok", tool_name=None, tool_args=None):
    tool_calls = []
    if tool_name:
        tool_calls = [
            {
                "id": "call_1",
                "type": "function",
                "function": {
                    "name": tool_name,
                    "arguments": json.dumps(tool_args or {}),
                },
            }
        ]
    return {"content": reply, "tool_calls": tool_calls}


def _request(content="Qualifique este lead"):
    return LeadQualificationAssistantRequest(
        messages=[{"role": "user", "content": content}],
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


def test_lead_assistant_uses_lead_profile_and_tool_contract(db, sample_user, monkeypatch):
    _create_config(db, sample_user.company_id)
    captured = {}

    def fake_load(profile):
        captured["profile"] = profile
        return "LEAD KNOWLEDGE"

    def fake_call(messages, tools):
        captured["messages"] = messages
        captured["tools"] = tools
        return _mock_completion(reply="Me envie os dados do lead.")

    monkeypatch.setattr("app.modules.ai.service.load_caloni_knowledge", fake_load)
    monkeypatch.setattr("app.modules.ai.service.call_ai_provider_with_tools", fake_call)

    response = lead_qualification_assistant_turn(db, sample_user, _request())

    assert captured["profile"] == "lead_qualification"
    assert captured["messages"][0] == {"role": "system", "content": "LEAD KNOWLEDGE"}
    assert "Segmentos ICP: Tech, SaaS" in captured["messages"][2]["content"]
    assert captured["tools"][0]["function"]["name"] == "qualify_leads"
    parameters = captured["tools"][0]["function"]["parameters"]
    assert parameters["required"] == ["leads"]
    assert parameters["additionalProperties"] is False

    leads = parameters["properties"]["leads"]
    assert leads["minItems"] == 1

    lead_item = leads["items"]
    assert lead_item["additionalProperties"] is False
    assert lead_item["required"] == LEAD_QUALIFICATION_REQUIRED_FIELDS

    properties = lead_item["properties"]
    assert properties["company_size"]["enum"] == ["1-10", "11-50", "51-200", "200+"]
    assert properties["urgency"]["enum"] == ["alta", "media", "baixa"]
    assert properties["timing"]["enum"] == ["imediato", "30_dias", "45_dias", "mais_tarde"]
    assert properties["pain_level"]["enum"] == ["alta", "media", "baixa"]
    assert response.reply == "Me envie os dados do lead."
    assert response.tool_result is None


def test_lead_assistant_sends_config_queue_and_attachment_context(db, sample_user, monkeypatch):
    _create_config(db, sample_user.company_id)
    captured = {}

    def fake_call(messages, tools):
        captured["messages"] = messages
        return _mock_completion(reply="O primeiro lead ficou acima por urgencia.")

    monkeypatch.setattr("app.modules.ai.service.call_ai_provider_with_tools", fake_call)

    req = LeadQualificationAssistantRequest(
        messages=[
            {
                "role": "assistant",
                "content": "Fila priorizada pronta.",
                "payload": {
                    "kind": "lead_qualification_queue",
                    "summary": {
                        "totalLeads": 1,
                        "highestScore": 100,
                        "primaryAction": "abordar_agora",
                    },
                    "leads": [
                        {
                            "leadId": "lead-1",
                            "companyName": "ACME Ltda",
                            "contactName": "Ana Silva",
                            "score": 100,
                            "tier": "diamond",
                            "recommendedAction": "abordar_agora",
                            "qualificationReason": "Fit alto com o ICP.",
                            "risk": "Validar budget.",
                            "recommendedNextStep": "Abordar agora.",
                        }
                    ],
                },
            },
            {
                "role": "user",
                "content": "Por que o primeiro lead ficou no topo?",
                "attachments": [
                    {
                        "filename": "novos-leads.txt",
                        "mime_type": "text/plain",
                        "size_bytes": 24,
                        "text_content": "Novo lead: Beta Ops, dor alta",
                    }
                ],
            },
        ],
    )

    response = lead_qualification_assistant_turn(db, sample_user, req)

    system_context = "\n\n".join(
        message["content"]
        for message in captured["messages"]
        if message["role"] == "system"
    )
    assert response.reply == "O primeiro lead ficou acima por urgencia."
    assert "Segmentos ICP: Tech, SaaS" in system_context
    assert "Fila de leads ja qualificada nesta conversa" in system_context
    assert "empresa=ACME Ltda" in system_context
    assert "score=100" in system_context
    assert "Dados extraidos de anexos enviados ao Radar de Leads" in system_context
    assert "Novo lead: Beta Ops" in system_context


def test_lead_assistant_requires_company_config_without_calling_provider(db, sample_user, monkeypatch):
    def fail_provider(messages, tools):
        raise AssertionError("provider should not be called without lead qualification config")

    monkeypatch.setattr("app.modules.ai.service.call_ai_provider_with_tools", fail_provider)

    response = lead_qualification_assistant_turn(db, sample_user, _request())

    assert response.tool_result is None
    assert "configure" in response.reply.lower()
    assert "radar de leads" in response.reply.lower()


def test_lead_assistant_creates_real_lead_and_ignores_model_score(db, sample_user, monkeypatch):
    _create_config(db, sample_user.company_id)
    monkeypatch.setattr(
        "app.modules.ai.service.call_ai_provider_with_tools",
        lambda messages, tools: _mock_completion(
            reply="Qualifiquei o lead e organizei a prioridade.",
            tool_name="qualify_leads",
            tool_args={
                "leads": [
                    {
                        "contact_name": "Ana Silva",
                        "company_name": "ACME Ltda",
                        "contact_role": "Founder",
                        "segment": "Tech",
                        "company_size": "11-50",
                        "urgency": "alta",
                        "timing": "imediato",
                        "pain_level": "alta",
                        "notes": "Inbound quente",
                        "qualification_reason": "Tem fit com ICP, decisor claro e dor urgente.",
                        "risk": "Validar budget antes da proposta.",
                        "recommended_next_step": "Abordar agora com diagnostico objetivo.",
                        "score": 3,
                    }
                ]
            },
        ),
    )

    response = lead_qualification_assistant_turn(db, sample_user, _request())

    assert response.reply == "Qualifiquei o lead e montei a prioridade abaixo."
    assert response.tool_result.kind == "lead_qualification_queue"
    assert response.tool_result.summary.total_leads == 1
    assert response.tool_result.summary.highest_score == 100
    assert response.tool_result.summary.primary_action == LeadAction.abordar_agora
    lead = response.tool_result.leads[0]
    assert lead.company_name == "ACME Ltda"
    assert lead.score == 100
    assert lead.tier.value == "diamond"
    assert lead.recommended_action == LeadAction.abordar_agora
    assert lead.qualification_reason == "Tem fit com ICP, decisor claro e dor urgente."
    assert lead.risk == "Validar budget antes da proposta."
    assert lead.recommended_next_step == "Abordar agora com diagnostico objetivo."
    assert uuid.UUID(lead.lead_id)


def test_lead_assistant_ignores_contradictory_provider_reply_after_scoring(db, sample_user, monkeypatch):
    _create_config(db, sample_user.company_id)
    monkeypatch.setattr(
        "app.modules.ai.service.call_ai_provider_with_tools",
        lambda messages, tools: _mock_completion(
            reply="Score 3, nutrir este lead.",
            tool_name="qualify_leads",
            tool_args={
                "leads": [
                    {
                        "contact_name": "Ana Silva",
                        "company_name": "ACME Ltda",
                        "contact_role": "Founder",
                        "segment": "Tech",
                        "company_size": "11-50",
                        "urgency": "alta",
                        "timing": "imediato",
                        "pain_level": "alta",
                        "qualification_reason": "Fit com ICP.",
                        "risk": "Validar budget.",
                        "recommended_next_step": "Abordar agora.",
                    }
                ]
            },
        ),
    )

    response = lead_qualification_assistant_turn(db, sample_user, _request())

    assert response.reply == "Qualifiquei o lead e montei a prioridade abaixo."
    assert "Score 3" not in response.reply
    assert response.tool_result.summary.highest_score == 100
    assert response.tool_result.summary.primary_action == LeadAction.abordar_agora


def test_lead_assistant_returns_multiple_leads_sorted_by_score(db, sample_user, monkeypatch):
    _create_config(db, sample_user.company_id)
    monkeypatch.setattr(
        "app.modules.ai.service.call_ai_provider_with_tools",
        lambda messages, tools: _mock_completion(
            reply="Montei a fila priorizada.",
            tool_name="qualify_leads",
            tool_args={
                "leads": [
                    {
                        "contact_name": "Bruno Baixo",
                        "company_name": "Loja Delta",
                        "contact_role": "Analista",
                        "segment": "Varejo",
                        "company_size": "1-10",
                        "urgency": "baixa",
                        "timing": "mais_tarde",
                        "pain_level": "baixa",
                        "notes": "Lead frio",
                        "qualification_reason": "Poucos sinais de fit com o ICP configurado.",
                        "risk": "Pode consumir tempo comercial sem prioridade real.",
                        "recommended_next_step": "Nutrir com conteudo e revisar depois.",
                    },
                    {
                        "contact_name": "Carla Forte",
                        "company_name": "SaaS Forte",
                        "contact_role": "Founder",
                        "segment": "SaaS",
                        "company_size": "51-200",
                        "urgency": "alta",
                        "timing": "30_dias",
                        "pain_level": "alta",
                        "notes": "Pedido veio por indicacao",
                        "qualification_reason": "Fit alto, decisora e problema urgente.",
                        "risk": "Confirmar processo de decisao e verba.",
                        "recommended_next_step": "Abordar agora e agendar diagnostico.",
                    },
                ]
            },
        ),
    )

    response = lead_qualification_assistant_turn(db, sample_user, _request("Tenho dois leads"))

    assert [lead.company_name for lead in response.tool_result.leads] == ["SaaS Forte", "Loja Delta"]
    assert [lead.score for lead in response.tool_result.leads] == [100, 0]
    assert response.tool_result.summary.total_leads == 2
    assert response.tool_result.summary.highest_score == 100
    assert response.tool_result.summary.primary_action == LeadAction.abordar_agora


def test_lead_assistant_rejects_invalid_batch_without_creating_partial_leads(db, sample_user, monkeypatch):
    _create_config(db, sample_user.company_id)
    monkeypatch.setattr(
        "app.modules.ai.service.call_ai_provider_with_tools",
        lambda messages, tools: _mock_completion(
            reply="",
            tool_name="qualify_leads",
            tool_args={
                "leads": [
                    {
                        "contact_name": "Ana Silva",
                        "company_name": "ACME Ltda",
                        "contact_role": "Founder",
                        "segment": "Tech",
                        "company_size": "11-50",
                        "urgency": "alta",
                        "timing": "imediato",
                        "pain_level": "alta",
                        "notes": "Inbound quente",
                        "qualification_reason": "Tem fit com ICP, decisor claro e dor urgente.",
                        "risk": "Validar budget antes da proposta.",
                        "recommended_next_step": "Abordar agora com diagnostico objetivo.",
                    },
                    {
                        "contact_name": "Lead Invalido",
                        "company_name": "Empresa Invalida",
                        "contact_role": "Founder",
                        "segment": "Tech",
                        "company_size": "500+",
                        "urgency": "alta",
                        "timing": "imediato",
                        "pain_level": "alta",
                        "qualification_reason": "Payload invalido.",
                        "risk": "Payload invalido.",
                        "recommended_next_step": "Payload invalido.",
                    },
                ]
            },
        ),
    )

    response = lead_qualification_assistant_turn(db, sample_user, _request("Tenho dois leads"))

    persisted_count = (
        db.query(QualifiedLead)
        .filter(QualifiedLead.company_id == sample_user.company_id)
        .count()
    )
    assert response.tool_result is None
    assert (
        "preciso" in response.reply.lower()
        or "qualificar com seguranca" in response.reply.lower()
    )
    assert persisted_count == 0


def test_lead_assistant_rejects_blank_required_string_without_creating_partial_leads(db, sample_user, monkeypatch):
    _create_config(db, sample_user.company_id)
    monkeypatch.setattr(
        "app.modules.ai.service.call_ai_provider_with_tools",
        lambda messages, tools: _mock_completion(
            reply="",
            tool_name="qualify_leads",
            tool_args={
                "leads": [
                    {
                        "contact_name": "Ana Silva",
                        "company_name": "ACME Ltda",
                        "contact_role": "Founder",
                        "segment": "Tech",
                        "company_size": "11-50",
                        "urgency": "alta",
                        "timing": "imediato",
                        "pain_level": "alta",
                        "qualification_reason": "Tem fit com ICP, decisor claro e dor urgente.",
                        "risk": "Validar budget antes da proposta.",
                        "recommended_next_step": "Abordar agora com diagnostico objetivo.",
                    },
                    {
                        "contact_name": "Lead Sem Empresa",
                        "company_name": "   ",
                        "contact_role": "Founder",
                        "segment": "Tech",
                        "company_size": "11-50",
                        "urgency": "alta",
                        "timing": "imediato",
                        "pain_level": "alta",
                        "qualification_reason": "Payload invalido.",
                        "risk": "Payload invalido.",
                        "recommended_next_step": "Payload invalido.",
                    },
                ]
            },
        ),
    )

    response = lead_qualification_assistant_turn(db, sample_user, _request("Tenho dois leads"))

    persisted_count = (
        db.query(QualifiedLead)
        .filter(QualifiedLead.company_id == sample_user.company_id)
        .count()
    )
    assert response.tool_result is None
    assert "qualificar com seguranca" in response.reply.lower()
    assert persisted_count == 0


def test_lead_assistant_rejects_oversized_persisted_string_without_creating_partial_leads(db, sample_user, monkeypatch):
    _create_config(db, sample_user.company_id)
    monkeypatch.setattr(
        "app.modules.ai.service.call_ai_provider_with_tools",
        lambda messages, tools: _mock_completion(
            reply="",
            tool_name="qualify_leads",
            tool_args={
                "leads": [
                    {
                        "contact_name": "Ana Silva",
                        "company_name": "ACME Ltda",
                        "contact_role": "Founder",
                        "segment": "Tech",
                        "company_size": "11-50",
                        "urgency": "alta",
                        "timing": "imediato",
                        "pain_level": "alta",
                        "qualification_reason": "Tem fit com ICP, decisor claro e dor urgente.",
                        "risk": "Validar budget antes da proposta.",
                        "recommended_next_step": "Abordar agora com diagnostico objetivo.",
                    },
                    {
                        "contact_name": "Lead Empresa Grande",
                        "company_name": "A" * 300,
                        "contact_role": "Founder",
                        "segment": "Tech",
                        "company_size": "11-50",
                        "urgency": "alta",
                        "timing": "imediato",
                        "pain_level": "alta",
                        "qualification_reason": "Payload invalido.",
                        "risk": "Payload invalido.",
                        "recommended_next_step": "Payload invalido.",
                    },
                ]
            },
        ),
    )

    response = lead_qualification_assistant_turn(db, sample_user, _request("Tenho dois leads"))

    persisted_count = (
        db.query(QualifiedLead)
        .filter(QualifiedLead.company_id == sample_user.company_id)
        .count()
    )
    assert response.tool_result is None
    assert persisted_count == 0


@pytest.mark.parametrize(
    ("field", "invalid_value"),
    [
        ("company_size", "500+"),
        ("urgency", "urgentissima"),
        ("timing", "15_dias"),
        ("pain_level", "critica"),
    ],
)
def test_lead_extract_rejects_invalid_controlled_values(field, invalid_value):
    lead_data = {
        "contact_name": "Ana Silva",
        "company_name": "Acme",
        "contact_role": "Founder",
        "segment": "SaaS",
        "company_size": "11-50",
        "urgency": "alta",
        "timing": "imediato",
        "pain_level": "alta",
        "qualification_reason": "Fit forte com ICP.",
        "risk": "Orcamento ainda nao confirmado.",
        "recommended_next_step": "Agendar diagnostico.",
    }
    lead_data[field] = invalid_value

    with pytest.raises(ValidationError):
        LeadQualificationLeadExtract(**lead_data)
