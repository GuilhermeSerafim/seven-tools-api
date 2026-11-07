from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session as DbSession

from app.models.lead_qualification import LeadQualificationConfig, QualifiedLead
from app.models.user import User
from app.modules.lead_qualification.scoring import score_lead, validate_config

LEAD_MUTABLE_FIELDS = (
    "contact_name",
    "company_name",
    "contact_role",
    "segment",
    "company_size",
    "urgency",
    "timing",
    "pain_level",
    "notes",
)

SCORE_INPUT_FIELDS = (
    "contact_role",
    "segment",
    "company_size",
    "urgency",
    "timing",
    "pain_level",
)


def _config_validation_error(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=message)


def _require_valid_config(config: LeadQualificationConfig) -> None:
    try:
        validate_config(config)
    except ValueError as exc:
        raise _config_validation_error(str(exc)) from exc


def _build_scoring_snapshot(config: LeadQualificationConfig, lead_data: dict[str, str], result) -> dict[str, object]:
    return {
        "score": result.score,
        "tier": result.tier.value,
        "recommended_action": result.recommended_action.value,
        "matches": dict(result.matches),
        "inputs": {
            "segment": lead_data["segment"],
            "company_size": lead_data["company_size"],
            "contact_role": lead_data["contact_role"],
            "urgency": lead_data["urgency"],
            "timing": lead_data["timing"],
            "pain_level": lead_data["pain_level"],
        },
        "weights": {
            "segment": config.weight_segment,
            "company_size": config.weight_company_size,
            "role": config.weight_role,
            "urgency": config.weight_urgency,
            "timing": config.weight_timing,
            "pain_level": config.weight_pain_level,
        },
        "thresholds": {
            "bronze_max": config.bronze_max,
            "silver_max": config.silver_max,
            "gold_max": config.gold_max,
        },
    }


def _lead_data_from_object(lead: QualifiedLead) -> dict[str, str]:
    return {
        "contact_name": lead.contact_name,
        "company_name": lead.company_name,
        "contact_role": lead.contact_role,
        "segment": lead.segment,
        "company_size": lead.company_size,
        "urgency": lead.urgency,
        "timing": lead.timing,
        "pain_level": lead.pain_level,
    }


def get_config_by_company_id(db: DbSession, company_id: uuid.UUID) -> LeadQualificationConfig | None:
    return (
        db.query(LeadQualificationConfig)
        .filter(LeadQualificationConfig.company_id == company_id)
        .first()
    )


def upsert_config_by_company_id(
    db: DbSession,
    company_id: uuid.UUID,
    data: dict,
) -> LeadQualificationConfig:
    config = get_config_by_company_id(db, company_id)
    candidate = {**data}
    if config is None:
        candidate["company_id"] = company_id
        new_config = LeadQualificationConfig(id=uuid.uuid4(), **candidate)
        _require_valid_config(new_config)
        db.add(new_config)
        db.commit()
        db.refresh(new_config)
        return new_config

    temp_config = LeadQualificationConfig(
        id=config.id,
        company_id=company_id,
        **candidate,
    )
    _require_valid_config(temp_config)
    for key, value in candidate.items():
        setattr(config, key, value)
    db.commit()
    db.refresh(config)
    return config


def list_leads(
    db: DbSession,
    company_id: uuid.UUID,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[QualifiedLead], int]:
    query = db.query(QualifiedLead).filter(QualifiedLead.company_id == company_id)
    total = query.count()
    items = (
        query.order_by(QualifiedLead.updated_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return items, total


def get_lead(db: DbSession, company_id: uuid.UUID, lead_id: uuid.UUID) -> QualifiedLead | None:
    return (
        db.query(QualifiedLead)
        .filter(QualifiedLead.id == lead_id, QualifiedLead.company_id == company_id)
        .first()
    )


def create_lead(
    db: DbSession,
    user: User,
    data: dict,
) -> QualifiedLead:
    if user.company_id is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Empresa do usuário não configurada.")

    config = get_config_by_company_id(db, user.company_id)
    if config is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Configuração de qualificação de leads não configurada.")
    _require_valid_config(config)

    lead_data = {**data}
    result = score_lead(config, lead_data)
    lead = QualifiedLead(
        id=uuid.uuid4(),
        company_id=user.company_id,
        created_by_user_id=user.id,
        **lead_data,
        score=result.score,
        tier=result.tier,
        recommended_action=result.recommended_action,
        scoring_snapshot=_build_scoring_snapshot(config, lead_data, result),
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


def patch_lead(
    db: DbSession,
    lead: QualifiedLead,
    data: dict,
) -> QualifiedLead:
    if lead.company_id is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Empresa do lead não configurada.")

    score_inputs_changed = False
    for field in LEAD_MUTABLE_FIELDS:
        if field in data and (data[field] is not None or field == "notes"):
            new_value = data[field]
            if getattr(lead, field) != new_value:
                setattr(lead, field, new_value)
                if field in SCORE_INPUT_FIELDS:
                    score_inputs_changed = True

    if "status" in data and data["status"] is not None:
        lead.status = data["status"]

    if score_inputs_changed:
        config = get_config_by_company_id(db, lead.company_id)
        if config is None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Configuração de qualificação de leads não configurada.")
        _require_valid_config(config)
        lead_data = _lead_data_from_object(lead)
        result = score_lead(config, lead_data)
        lead.score = result.score
        lead.tier = result.tier
        lead.recommended_action = result.recommended_action
        lead.scoring_snapshot = _build_scoring_snapshot(config, lead_data, result)

    db.commit()
    db.refresh(lead)
    return lead
