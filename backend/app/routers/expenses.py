from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..db import get_db
from ..deps import current_user, get_owned_account

router = APIRouter(prefix="/expenses", tags=["expenses"])


@router.get("", response_model=list[schemas.ExpenseOut])
def list_expenses(
    account: models.WBAccount = Depends(get_owned_account),
    db: Session = Depends(get_db),
):
    return (
        db.query(models.Expense)
        .filter(models.Expense.account_id == account.id)
        .order_by(models.Expense.date_from.desc())
        .all()
    )


@router.post("", response_model=schemas.ExpenseOut)
def create_expense(
    data: schemas.ExpenseIn,
    account: models.WBAccount = Depends(get_owned_account),
    db: Session = Depends(get_db),
):
    e = models.Expense(account_id=account.id, **data.model_dump())
    db.add(e); db.commit(); db.refresh(e)
    return e


@router.delete("/{expense_id}", status_code=204)
def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(current_user),
):
    e = db.get(models.Expense, expense_id)
    if not e:
        raise HTTPException(404)
    acc = db.get(models.WBAccount, e.account_id)
    if not acc or acc.user_id != user.id:
        raise HTTPException(404)
    db.delete(e); db.commit()
