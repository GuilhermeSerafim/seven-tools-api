# seven_tools_api/app/modules/proposals/service.py
import uuid

from sqlalchemy.orm import Session as DbSession

from app.models.proposal import Proposal


def create_proposal(db: DbSession, user_id: uuid.UUID, data: dict) -> Proposal:
    proposal = Proposal(id=uuid.uuid4(), user_id=user_id, **data)
    db.add(proposal)
    db.commit()
    db.refresh(proposal)
    return proposal


def list_proposals(
    db: DbSession,
    user_id: uuid.UUID,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[Proposal], int]:
    query = db.query(Proposal).filter(Proposal.user_id == user_id)
    total = query.count()
    items = (
        query
        .order_by(Proposal.updated_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return items, total


def get_proposal(db: DbSession, user_id: uuid.UUID, proposal_id: uuid.UUID) -> Proposal | None:
    return db.query(Proposal).filter(
        Proposal.id == proposal_id,
        Proposal.user_id == user_id,
    ).first()


def patch_proposal(db: DbSession, proposal: Proposal, data: dict) -> Proposal:
    for key, value in data.items():
        if value is not None:
            setattr(proposal, key, value)
    db.commit()
    db.refresh(proposal)
    return proposal


def delete_proposal(db: DbSession, proposal: Proposal) -> None:
    db.delete(proposal)
    db.commit()
