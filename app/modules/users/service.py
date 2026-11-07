# seven_tools_api/app/modules/users/service.py
import uuid

from sqlalchemy import func
from sqlalchemy.orm import Session as DbSession

from app.models.company import Company
from app.models.favorite import Favorite
from app.models.user import User


def update_user(db: DbSession, user: User, data: dict) -> tuple[User | None, str | None]:
    new_email = data.get("email")
    if new_email is not None:
        existing = db.query(User).filter(
            func.lower(User.email) == new_email,
            User.id != user.id,
        ).first()
        if existing is not None:
            return None, "EMAIL_EXISTS"

    for key, value in data.items():
        if value is not None:
            setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user, None


def update_company(db: DbSession, company_id: uuid.UUID, data: dict) -> Company | None:
    company = db.query(Company).filter(Company.id == company_id).first()
    if company is None:
        return None
    for key, value in data.items():
        if value is not None:
            setattr(company, key, value)
    db.commit()
    db.refresh(company)
    return company


def get_favorites(db: DbSession, user_id: uuid.UUID) -> list[str]:
    favorites = db.query(Favorite).filter(Favorite.user_id == user_id).all()
    return [f.tool_slug for f in favorites]


def add_favorite(db: DbSession, user_id: uuid.UUID, tool_slug: str) -> bool:
    existing = db.query(Favorite).filter(
        Favorite.user_id == user_id,
        Favorite.tool_slug == tool_slug,
    ).first()
    if existing:
        return False

    fav = Favorite(id=uuid.uuid4(), user_id=user_id, tool_slug=tool_slug)
    db.add(fav)
    db.commit()
    return True


def remove_favorite(db: DbSession, user_id: uuid.UUID, tool_slug: str) -> bool:
    fav = db.query(Favorite).filter(
        Favorite.user_id == user_id,
        Favorite.tool_slug == tool_slug,
    ).first()
    if fav is None:
        return False
    db.delete(fav)
    db.commit()
    return True
