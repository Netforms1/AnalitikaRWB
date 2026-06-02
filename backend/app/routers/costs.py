from datetime import date
from decimal import Decimal
from io import BytesIO

import pandas as pd
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from .. import models, schemas
from ..db import get_db
from ..deps import current_user, get_owned_account

router = APIRouter(prefix="/costs", tags=["costs"])


@router.get("", response_model=list[schemas.CostPriceOut])
def list_costs(
    account: models.WBAccount = Depends(get_owned_account),
    db: Session = Depends(get_db),
):
    return (
        db.query(models.CostPrice)
        .filter(models.CostPrice.account_id == account.id)
        .order_by(models.CostPrice.nm_id, models.CostPrice.valid_from.desc())
        .all()
    )


@router.post("", response_model=schemas.CostPriceOut)
def create_cost(
    data: schemas.CostPriceIn,
    account: models.WBAccount = Depends(get_owned_account),
    db: Session = Depends(get_db),
):
    account_id = account.id
    if data.nm_id is None and not data.sa_name:
        raise HTTPException(400, "nm_id or sa_name required")
    # Закрываем предыдущую запись по этому ключу
    q = db.query(models.CostPrice).filter(
        models.CostPrice.account_id == account_id,
        models.CostPrice.valid_to.is_(None),
    )
    if data.nm_id is not None:
        q = q.filter(models.CostPrice.nm_id == data.nm_id)
    elif data.sa_name:
        q = q.filter(models.CostPrice.sa_name == data.sa_name)
    for prev in q.all():
        prev.valid_to = data.valid_from

    cp = models.CostPrice(account_id=account_id, **data.model_dump())
    db.add(cp)
    db.commit()
    db.refresh(cp)
    return cp


@router.delete("/{cost_id}", status_code=204)
def delete_cost(
    cost_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(current_user),
):
    cp = db.get(models.CostPrice, cost_id)
    if not cp:
        raise HTTPException(404)
    acc = db.get(models.WBAccount, cp.account_id)
    if not acc or acc.user_id != user.id:
        raise HTTPException(404)
    db.delete(cp); db.commit()


@router.post("/upload")
async def upload_costs(
    account_id: int = Form(...),
    valid_from: date = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: models.User = Depends(current_user),
):
    acc = db.get(models.WBAccount, account_id)
    if not acc or acc.user_id != user.id:
        raise HTTPException(404, "Account not found")
    """Массовая загрузка из Excel/CSV. Колонки: nm_id (или sa_name), cost."""
    content = await file.read()
    name = (file.filename or "").lower()
    try:
        if name.endswith(".csv"):
            df = pd.read_csv(BytesIO(content))
        else:
            df = pd.read_excel(BytesIO(content))
    except Exception as e:
        raise HTTPException(400, f"Failed to parse file: {e}")
    cols = {c.lower(): c for c in df.columns}
    nm_col = cols.get("nm_id") or cols.get("артикул wb") or cols.get("артикулwb")
    sa_col = cols.get("sa_name") or cols.get("артикул") or cols.get("артикул поставщика")
    cost_col = cols.get("cost") or cols.get("себестоимость")
    if not cost_col or not (nm_col or sa_col):
        raise HTTPException(400, "Need cost and one of: nm_id/sa_name columns")

    created = 0
    for _, row in df.iterrows():
        nm_id = int(row[nm_col]) if nm_col and pd.notna(row[nm_col]) else None
        sa = str(row[sa_col]) if sa_col and pd.notna(row[sa_col]) else None
        try:
            cost = Decimal(str(row[cost_col]))
        except Exception:
            continue
        # close previous
        q = db.query(models.CostPrice).filter(
            models.CostPrice.account_id == account_id,
            models.CostPrice.valid_to.is_(None),
        )
        if nm_id is not None:
            q = q.filter(models.CostPrice.nm_id == nm_id)
        elif sa:
            q = q.filter(models.CostPrice.sa_name == sa)
        else:
            continue
        for prev in q.all():
            prev.valid_to = valid_from
        db.add(models.CostPrice(
            account_id=account_id, nm_id=nm_id, sa_name=sa,
            cost=cost, valid_from=valid_from,
        ))
        created += 1
    db.commit()
    return {"created": created}
