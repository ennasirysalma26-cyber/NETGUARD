from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import (
    verify_password, hash_password,
    create_access_token, create_refresh_token,
    decode_token, get_current_user, ACCESS_EXPIRE,
)
from app.models.models import User
from app.schemas.schemas import (
    LoginRequest, TokenResponse, RefreshRequest,
    AccessTokenResponse, UserOut,
)

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User).where(User.username == data.username)
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants invalides",
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Compte désactivé")

    return TokenResponse(
        access_token=create_access_token(user.id, user.role),
        refresh_token=create_refresh_token(user.id),
        expires_in=ACCESS_EXPIRE * 60,
    )


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    payload = decode_token(data.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Token de rafraîchissement invalide")

    result = await db.execute(select(User).where(User.id == payload["sub"]))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="Utilisateur introuvable")

    return AccessTokenResponse(
        access_token=create_access_token(user.id, user.role),
        expires_in=ACCESS_EXPIRE * 60,
    )


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    # En production : ajouter le token à une blacklist Redis
    return {"message": "Déconnecté avec succès"}


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)):
    return current_user
