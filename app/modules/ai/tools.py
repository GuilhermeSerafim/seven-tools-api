PROPOSAL_PATCH_PROPERTIES = {
    "title": {"type": "string"},
    "clientName": {"type": "string"},
    "clientCompany": {"type": "string"},
    "clientEmail": {"type": "string"},
    "clientPhone": {"type": "string"},
    "projectDescription": {"type": "string"},
    "scope": {"type": "string"},
    "value": {"type": "string"},
    "deadline": {"type": "string"},
    "notes": {"type": "string"},
}

PROPOSAL_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "patch_draft",
            "description": (
                "Atualiza campos do draft de proposta em construção. "
                "Use quando coletar dado novo do usuário, antes da proposta ser salva."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "patch": {
                        "type": "object",
                        "properties": PROPOSAL_PATCH_PROPERTIES,
                        "additionalProperties": False,
                    }
                },
                "required": ["patch"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "request_validation",
            "description": (
                "Pede análise determinística de uma proposta SALVA (precisa de proposal_id). "
                "Use quando o usuário pedir validação ou feedback sobre proposta existente."
            ),
            "parameters": {
                "type": "object",
                "properties": {"proposal_id": {"type": "string"}},
                "required": ["proposal_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "request_save",
            "description": (
                "Sinaliza que o draft está pronto e pede confirmação para persistir. "
                "So use quando title, clientName, clientCompany, clientEmail, "
                "clientPhone, projectDescription, scope, value e deadline estiverem preenchidos."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "request_update",
            "description": (
                "Edita uma proposta JÁ SALVA. Use quando current_proposal_id estiver presente "
                "e o usuário pedir alteração de campo."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "patch": {
                        "type": "object",
                        "properties": PROPOSAL_PATCH_PROPERTIES,
                        "additionalProperties": False,
                    }
                },
                "required": ["patch"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "open_existing",
            "description": "Carrega uma proposta existente pelo ID (frontend navega).",
            "parameters": {
                "type": "object",
                "properties": {"proposal_id": {"type": "string"}},
                "required": ["proposal_id"],
                "additionalProperties": False,
            },
        },
    },
]

LEAD_QUALIFICATION_LEAD_PROPERTIES = {
    "contact_name": {"type": "string"},
    "company_name": {"type": "string"},
    "contact_role": {"type": "string"},
    "segment": {"type": "string"},
    "company_size": {"type": "string", "enum": ["1-10", "11-50", "51-200", "200+"]},
    "urgency": {"type": "string", "enum": ["alta", "media", "baixa"]},
    "timing": {"type": "string", "enum": ["imediato", "30_dias", "45_dias", "mais_tarde"]},
    "pain_level": {"type": "string", "enum": ["alta", "media", "baixa"]},
    "notes": {"type": "string"},
    "qualification_reason": {"type": "string"},
    "risk": {"type": "string"},
    "recommended_next_step": {"type": "string"},
}

LEAD_QUALIFICATION_REQUIRED_FIELDS = [
    "contact_name",
    "company_name",
    "contact_role",
    "segment",
    "company_size",
    "urgency",
    "timing",
    "pain_level",
    "qualification_reason",
    "risk",
    "recommended_next_step",
]

LEAD_QUALIFICATION_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "qualify_leads",
            "description": (
                "Extrai um ou mais leads completos de texto livre para o backend "
                "criar leads reais e calcular score deterministico. Use somente "
                "quando todos os campos obrigatorios de cada lead estiverem claros."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "leads": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": LEAD_QUALIFICATION_LEAD_PROPERTIES,
                            "required": LEAD_QUALIFICATION_REQUIRED_FIELDS,
                            "additionalProperties": False,
                        },
                        "minItems": 1,
                    }
                },
                "required": ["leads"],
                "additionalProperties": False,
            },
        },
    }
]

COMMERCIAL_DIAGNOSIS_REPORT_PROPERTIES = {
    "cenario": {"type": "string"},
    "gargalo_principal": {"type": "string"},
    "etapa_critica_funil": {"type": "string"},
    "sintomas": {
        "type": "array",
        "items": {"type": "string"},
        "minItems": 2,
    },
    "causa_provavel": {"type": "string"},
    "acao_recomendada": {"type": "string"},
    "plano_prioritario": {
        "type": "array",
        "items": {"type": "string"},
        "minItems": 2,
    },
}

COMMERCIAL_DIAGNOSIS_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "submit_commercial_diagnosis_report",
            "description": (
                "Use apenas quando houver contexto suficiente ou quando o usuario pedir uma "
                "consolidacao do diagnostico comercial. Nao use em todos os turnos."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "report": {
                        "type": "object",
                        "properties": COMMERCIAL_DIAGNOSIS_REPORT_PROPERTIES,
                        "required": [
                            "cenario",
                            "gargalo_principal",
                            "etapa_critica_funil",
                            "sintomas",
                            "causa_provavel",
                            "acao_recomendada",
                            "plano_prioritario",
                        ],
                        "additionalProperties": False,
                    }
                },
                "required": ["report"],
                "additionalProperties": False,
            },
        },
    }
]
