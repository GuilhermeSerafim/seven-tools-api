# seven_tools_api/app/schemas/ai.py
from pydantic import BaseModel


# --- Validate Proposal ---

class ValidateProposalRequest(BaseModel):
    file_name: str
    file_content: str


class CalonCriterion(BaseModel):
    name: str
    score: float
    comment: str


class ValidateProposalResponse(BaseModel):
    overall_score: float
    overall_label: str
    strong_points: list[str]
    weak_points: list[str]
    criteria: list[CalonCriterion]
    suggestions: list[str]


# --- Diagnose ---

class DiagnoseRequest(BaseModel):
    nicho: str
    perfil_cliente: str
    ticket_medio: str
    receita_atual: str
    meta_receita: str
    desafio: str
    gargalo: str
    objecoes_comuns: str
    processo_venda: str


class DiagnoseResponse(BaseModel):
    saude_comercial: float
    label_saude: str
    diagnostico_geral: str
    principal_erro: str
    etapa_critica_funil: str
    sintomas: list[str]
    ajuste_recomendado: str
    orientacao_imediata: str
    plano_de_acao: list[str]
    metricas_chave: list[str]
