from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import schemas
from ..db import get_db
from ..services import profit

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary", response_model=schemas.ProfitSummary)
def summary(account_id: int, date_from: date, date_to: date, db: Session = Depends(get_db)):
    return profit.compute_summary(db, account_id, date_from, date_to)


@router.get("/by-sku", response_model=list[schemas.SkuProfitRow])
def by_sku(account_id: int, date_from: date, date_to: date, db: Session = Depends(get_db)):
    return profit.compute_by_sku(db, account_id, date_from, date_to)


@router.get("/weekly", response_model=list[schemas.WeeklyPoint])
def weekly(account_id: int, date_from: date, date_to: date, db: Session = Depends(get_db)):
    return profit.compute_weekly(db, account_id, date_from, date_to)


@router.get("/compare", response_model=schemas.PeriodCompare)
def compare(account_id: int, date_from: date, date_to: date, db: Session = Depends(get_db)):
    return profit.compute_compare(db, account_id, date_from, date_to)
