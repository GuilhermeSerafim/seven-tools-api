from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session as DbSession

from app.dependencies import get_current_approved_user, get_db
from app.models.user import User
from app.modules.lead_qualification.service import (
    create_lead,
    get_config_by_company_id,
    get_lead,
    list_leads,
    patch_lead,
    upsert_config_by_company_id,
)
from app.schemas.lead_qualification import (
    LeadQualificationConfigResponse,
    LeadQualificationConfigUpsert,
    PaginatedQualifiedLeadResponse,
    QualifiedLeadCreate,
    QualifiedLeadPatch,
    QualifiedLeadResponse,
)

router = APIRouter(prefix="/lead-qualification", tags=["lead-qualification"])


@router.put("/config", response_model=LeadQualificationConfigResponse)
def put_config(
    body: LeadQualificationConfigUpsert,
    user: User = Depends(get_current_approved_user),
    db: DbSession = Depends(get_db),
):
    if user.company_id is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Empresa do usuário não configurada.")
    return upsert_config_by_company_id(db, user.company_id, body.model_dump())


@router.get("/config", response_model=LeadQualificationConfigResponse)
def get_config(
    user: User = Depends(get_current_approved_user),
    db: DbSession = Depends(get_db),
):
    if user.company_id is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Empresa do usuário não configurada.")
    config = get_config_by_company_id(db, user.company_id)
    if config is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Configuração de qualificação de leads não encontrada.")
    return config


@router.post("/leads", response_model=QualifiedLeadResponse, status_code=status.HTTP_201_CREATED)
def post_lead(
    body: QualifiedLeadCreate,
    user: User = Depends(get_current_approved_user),
    db: DbSession = Depends(get_db),
):
    return create_lead(db, user, body.model_dump())


@router.get("/leads", response_model=PaginatedQualifiedLeadResponse)
def list_all(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_approved_user),
    db: DbSession = Depends(get_db),
):
    if user.company_id is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Empresa do usuário não configurada.")
    items, total = list_leads(db, user.company_id, page, per_page)
    return PaginatedQualifiedLeadResponse(items=items, total=total, page=page, per_page=per_page)


@router.get("/leads/{lead_id}", response_model=QualifiedLeadResponse)
def get_one(
    lead_id: uuid.UUID,
    user: User = Depends(get_current_approved_user),
    db: DbSession = Depends(get_db),
):
    if user.company_id is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Empresa do usuário não configurada.")
    lead = get_lead(db, user.company_id, lead_id)
    if lead is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead não encontrado.")
    return lead


@router.patch("/leads/{lead_id}", response_model=QualifiedLeadResponse)
def patch_one(
    lead_id: uuid.UUID,
    body: QualifiedLeadPatch,
    user: User = Depends(get_current_approved_user),
    db: DbSession = Depends(get_db),
):
    if user.company_id is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Empresa do usuário não configurada.")
    lead = get_lead(db, user.company_id, lead_id)
    if lead is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead não encontrado.")
    return patch_lead(db, lead, body.model_dump(exclude_unset=True))
