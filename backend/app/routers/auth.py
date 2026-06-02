from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, EmailStr
from sqlalchemy.orm import Session

from .. import models
from ..db import get_db
from ..deps import current_user
from ..services import auth

router = APIRouter(prefix="/auth", tags=["auth"])


class CredsIn(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


@router.post("/register", response_model=TokenOut)
def register(data: CredsIn, db: Session = Depends(get_db)):
    if len(data.password) < 6:
        raise HTTPException(400, "Password must be at least 6 chars")
    if db.query(models.User).filter(models.User.email == data.email).first():
        raise HTTPException(409, "Email already registered")
    u = models.User(email=data.email, password_hash=auth.hash_password(data.password))
    db.add(u); db.commit(); db.refresh(u)
    return TokenOut(access_token=auth.create_token(u.id), user=UserOut.model_validate(u))


@router.post("/login", response_model=TokenOut)
def login(data: CredsIn, db: Session = Depends(get_db)):
    u = db.query(models.User).filter(models.User.email == data.email).first()
    if not u or not auth.verify_password(data.password, u.password_hash):
        raise HTTPException(401, "Invalid email or password")
    return TokenOut(access_token=auth.create_token(u.id), user=UserOut.model_validate(u))


@router.get("/me", response_model=UserOut)
def me(user: models.User = Depends(current_user)):
    return user
