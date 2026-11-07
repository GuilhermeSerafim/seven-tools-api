# seven_tools_api/app/modules/users/router.py
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DbSession

from app.dependencies import get_current_approved_user, get_current_user, get_db
from app.models.user import User
from app.modules.users.service import add_favorite, get_favorites, remove_favorite, update_company, update_user
from app.schemas.user import CompanyResponse, CompanyUpdate, FavoriteResponse, UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])

CurrentUserDep = Annotated[User, Depends(get_current_user)]
ApprovedUserDep = Annotated[User, Depends(get_current_approved_user)]
DbSessionDep = Annotated[DbSession, Depends(get_db)]


@router.get("/me", response_model=UserResponse)
def get_me(user: CurrentUserDep):
    return user


@router.put("/me", response_model=UserResponse)
def put_me(
    body: UserUpdate,
    user: ApprovedUserDep,
    db: DbSessionDep,
):
    updated, error_code = update_user(db, user, body.model_dump(exclude_unset=True))
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"detail": "E-mail já cadastrado.", "code": error_code},
        )
    return updated


@router.put("/me/company", response_model=CompanyResponse)
def put_my_company(
    body: CompanyUpdate,
    user: ApprovedUserDep,
    db: DbSessionDep,
):
    if user.company_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nenhuma empresa associada.")
    company = update_company(db, user.company_id, body.model_dump(exclude_unset=True))
    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empresa não encontrada.")
    return company


@router.get("/me/favorites", response_model=FavoriteResponse)
def list_favorites(
    user: ApprovedUserDep,
    db: DbSessionDep,
):
    slugs = get_favorites(db, user.id)
    return FavoriteResponse(tool_slugs=slugs)


@router.post("/me/favorites/{slug}", status_code=status.HTTP_201_CREATED)
def add_fav(
    slug: str,
    user: ApprovedUserDep,
    db: DbSessionDep,
):
    if not add_favorite(db, user.id, slug):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"detail": "Ferramenta já está nos favoritos.", "code": "DUPLICATE_FAVORITE"})
    return {"detail": "Favorito adicionado com sucesso."}


@router.delete("/me/favorites/{slug}")
def remove_fav(
    slug: str,
    user: ApprovedUserDep,
    db: DbSessionDep,
):
    if not remove_favorite(db, user.id, slug):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"detail": "Favorito não encontrado.", "code": "FAVORITE_NOT_FOUND"})
    return {"detail": "Favorito removido com sucesso."}
