# seven_tools_api/tests/test_ai.py
import json
from unittest.mock import patch

from app.modules.ai.service import validate_proposal_service

MOCK_DIAGNOSTIC_RESPONSE = json.dumps({
    "saudeComercial": 6.5,
    "labelSaude": "Atenção Necessária",
    "diagnosticoGeral": "A operação comercial apresenta pontos de melhoria.",
    "principalErro": "Falta de follow-up estruturado.",
    "etapaCriticaFunil": "Qualificação",
    "sintomas": ["Baixa conversão", "Ciclo longo", "Objeções recorrentes"],
    "ajusteRecomendado": "Implementar cadência de follow-up.",
    "orientacaoImediata": "Mapear todos os leads sem resposta nos últimos 7 dias.",
    "planoDeAcao": ["Revisar pipeline", "Criar cadência", "Treinar equipe"],
    "metricasChave": ["Taxa de resposta", "Tempo médio de ciclo"],
})


def test_diagnose(client, auth_headers):
    with (
        patch("app.modules.ai.service.load_caloni_knowledge", return_value="diagnostic knowledge") as mock_knowledge,
        patch("app.modules.ai.service.call_ai_provider") as mock_ai,
    ):
        mock_ai.return_value = MOCK_DIAGNOSTIC_RESPONSE

        response = client.post("/api/v1/ai/diagnose", headers=auth_headers, json={
            "nicho": "SaaS B2B",
            "perfil_cliente": "Empresas de 50-200 funcionários",
            "ticket_medio": "5000",
            "receita_atual": "50000",
            "meta_receita": "100000",
            "desafio": "Baixa conversão",
            "gargalo": "Qualificação de leads",
            "objecoes_comuns": "Preço alto",
            "processo_venda": "Inbound + SDR + closer",
        })

        assert response.status_code == 200
        data = response.json()
        assert data["saude_comercial"] == 6.5
        assert data["label_saude"] == "Atenção Necessária"
        assert len(data["sintomas"]) == 3
        assert len(data["plano_de_acao"]) == 3
        mock_knowledge.assert_called_once_with("diagnostic")
        mock_ai.assert_called_once()


def test_validate_proposal_service_uses_validation_profile(db, sample_user):
    mock_validation_response = json.dumps({
        "overallScore": 8,
        "overallLabel": "Boa proposta",
        "strongPoints": ["Escopo claro"],
        "weakPoints": ["Falta urgencia"],
        "criteria": [
            {"name": "Clareza da Proposta de Valor", "score": 8, "comment": "Clara"},
            {"name": "Urgencia e Escassez", "score": 6, "comment": "Pode melhorar"},
        ],
        "suggestions": ["Adicionar proximo passo objetivo"],
    })

    with (
        patch("app.modules.ai.service.load_caloni_knowledge", return_value="validation knowledge") as mock_knowledge,
        patch("app.modules.ai.service.call_ai_provider", return_value=mock_validation_response),
    ):
        result = validate_proposal_service(
            db,
            sample_user.id,
            "Proposta Acme",
            "Conteudo da proposta",
        )

    assert result["overall_score"] == 8
    mock_knowledge.assert_called_once_with("proposal_validation")
