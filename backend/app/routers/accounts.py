from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..db import get_db
from ..deps import current_user, get_owned_account

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("", response_model=list[schemas.AccountOut])
def list_accounts(db: Session = Depends(get_db), user: models.User = Depends(current_user)):
    return (
        db.query(models.WBAccount)
        .filter(models.WBAccount.user_id == user.id)
        .order_by(models.WBAccount.id)
        .all()
    )


@router.post("", response_model=schemas.AccountOut)
def create_account(
    data: schemas.AccountIn,
    db: Session = Depends(get_db),
    user: models.User = Depends(current_user),
):
    a = models.WBAccount(user_id=user.id, **data.model_dump())
    db.add(a); db.commit(); db.refresh(a)
    return a


@router.put("/{account_id}", response_model=schemas.AccountOut)
def update_account(
    data: schemas.AccountIn,
    a: models.WBAccount = Depends(get_owned_account),
    db: Session = Depends(get_db),
):
    for k, v in data.model_dump().items():
        setattr(a, k, v)
    db.commit(); db.refresh(a)
    return a


@router.delete("/{account_id}", status_code=204)
def delete_account(
    a: models.WBAccount = Depends(get_owned_account),
    db: Session = Depends(get_db),
):
    db.delete(a); db.commit()
