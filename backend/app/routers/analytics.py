from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas
from ..db import get_db
from ..deps import get_owned_account
from ..services import profit

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary", response_model=schemas.ProfitSummary)
def summary(
    date_from: date, date_to: date,
    account: models.WBAccount = Depends(get_owned_account),
    db: Session = Depends(get_db),
):
    return profit.compute_summary(db, account.id, date_from, date_to)


@router.get("/by-sku", response_model=list[schemas.SkuProfitRow])
def by_sku(
    date_from: date, date_to: date,
    account: models.WBAccount = Depends(get_owned_account),
    db: Session = Depends(get_db),
):
    return profit.compute_by_sku(db, account.id, date_from, date_to)


@router.get("/weekly", response_model=list[schemas.WeeklyPoint])
def weekly(
    date_from: date, date_to: date,
    account: models.WBAccount = Depends(get_owned_account),
    db: Session = Depends(get_db),
):
    return profit.compute_weekly(db, account.id, date_from, date_to)


@router.get("/compare", response_model=schemas.PeriodCompare)
def compare(
    date_from: date, date_to: date,
    account: models.WBAccount = Depends(get_owned_account),
    db: Session = Depends(get_db),
):
    return profit.compute_compare(db, account.id, date_from, date_to)
