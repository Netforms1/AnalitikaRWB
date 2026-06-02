"""Зависимости FastAPI: текущий пользователь, проверка владения аккаунтом."""
from __future__ import annotations

import jwt
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from . import models
from .db import get_db
from .services import auth


def current_user(request: Request, db: Session = Depends(get_db)) -> models.User:
    h = request.headers.get("Authorization") or ""
    if not h.lower().startswith("bearer "):
        raise HTTPException(401, "Not authenticated")
    token = h.split(None, 1)[1].strip()
    try:
        uid = auth.decode_token(token)
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid or expired token")
    user = db.get(models.User, uid)
    if not user:
        raise HTTPException(401, "User not found")
    return user


def get_owned_account(
    account_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(current_user),
) -> models.WBAccount:
    acc = db.get(models.WBAccount, account_id)
    if not acc or acc.user_id != user.id:
        raise HTTPException(404, "Account not found")
    return acc
