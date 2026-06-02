from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..db import get_db

router = APIRouter(prefix="/expenses", tags=["expenses"])


@router.get("", response_model=list[schemas.ExpenseOut])
def list_expenses(account_id: int, db: Session = Depends(get_db)):
    return (
        db.query(models.Expense)
        .filter(models.Expense.account_id == account_id)
        .order_by(models.Expense.date_from.desc())
        .all()
    )


@router.post("", response_model=schemas.ExpenseOut)
def create_expense(account_id: int, data: schemas.ExpenseIn, db: Session = Depends(get_db)):
    e = models.Expense(account_id=account_id, **data.model_dump())
    db.add(e)
    db.commit()
    db.refresh(e)
    return e


@router.delete("/{expense_id}", status_code=204)
def delete_expense(expense_id: int, db: Session = Depends(get_db)):
    e = db.get(models.Expense, expense_id)
    if not e:
        raise HTTPException(404)
    db.delete(e)
    db.commit()
