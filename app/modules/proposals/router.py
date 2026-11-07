# seven_tools_api/app/modules/proposals/router.py
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session as DbSession

from app.dependencies import get_current_approved_user, get_db
from app.models.user import User
from app.modules.proposals.service import create_proposal, delete_proposal, get_proposal, list_proposals, patch_proposal
from app.schemas.proposal import PaginatedProposalResponse, ProposalCreate, ProposalPatch, ProposalResponse

router = APIRouter(prefix="/proposals", tags=["proposals"])


@router.post("", response_model=ProposalResponse, status_code=status.HTTP_201_CREATED)
def create(
    body: ProposalCreate,
    user: User = Depends(get_current_approved_user),
    db: DbSession = Depends(get_db),
):
    proposal = create_proposal(db, user.id, body.model_dump())
    return proposal


@router.get("", response_model=PaginatedProposalResponse)
def list_all(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_approved_user),
    db: DbSession = Depends(get_db),
):
    items, total = list_proposals(db, user.id, page, per_page)
    return PaginatedProposalResponse(items=items, total=total, page=page, per_page=per_page)


@router.get("/{proposal_id}", response_model=ProposalResponse)
def get_one(
    proposal_id: uuid.UUID,
    user: User = Depends(get_current_approved_user),
    db: DbSession = Depends(get_db),
):
    proposal = get_proposal(db, user.id, proposal_id)
    if proposal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposta não encontrada.")
    return proposal


@router.patch("/{proposal_id}", response_model=ProposalResponse)
def patch_one(
    proposal_id: uuid.UUID,
    body: ProposalPatch,
    user: User = Depends(get_current_approved_user),
    db: DbSession = Depends(get_db),
):
    proposal = get_proposal(db, user.id, proposal_id)
    if proposal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposta não encontrada.")
    updated = patch_proposal(db, proposal, body.model_dump(exclude_unset=True))
    return updated


@router.delete("/{proposal_id}")
def delete_one(
    proposal_id: uuid.UUID,
    user: User = Depends(get_current_approved_user),
    db: DbSession = Depends(get_db),
):
    proposal = get_proposal(db, user.id, proposal_id)
    if proposal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposta não encontrada.")
    delete_proposal(db, proposal)
    return {"detail": "Proposta excluída com sucesso."}
