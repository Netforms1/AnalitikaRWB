from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..db import get_db

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("", response_model=list[schemas.AccountOut])
def list_accounts(db: Session = Depends(get_db)):
    return db.query(models.WBAccount).order_by(models.WBAccount.id).all()


@router.post("", response_model=schemas.AccountOut)
def create_account(data: schemas.AccountIn, db: Session = Depends(get_db)):
    a = models.WBAccount(**data.model_dump())
    db.add(a)
    db.commit()
    db.refresh(a)
    return a


@router.put("/{account_id}", response_model=schemas.AccountOut)
def update_account(account_id: int, data: schemas.AccountIn, db: Session = Depends(get_db)):
    a = db.get(models.WBAccount, account_id)
    if not a:
        raise HTTPException(404)
    for k, v in data.model_dump().items():
        setattr(a, k, v)
    db.commit()
    db.refresh(a)
    return a


@router.delete("/{account_id}", status_code=204)
def delete_account(account_id: int, db: Session = Depends(get_db)):
    a = db.get(models.WBAccount, account_id)
    if not a:
        raise HTTPException(404)
    db.delete(a)
    db.commit()
