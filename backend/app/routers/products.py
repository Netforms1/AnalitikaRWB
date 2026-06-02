from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from .. import models, schemas
from ..db import get_db
from ..deps import get_owned_account
from ..services import wb_content

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[schemas.ProductOut])
def list_products(
    account: models.WBAccount = Depends(get_owned_account),
    db: Session = Depends(get_db),
):
    return (
        db.query(models.Product)
        .filter(models.Product.account_id == account.id)
        .order_by(models.Product.title)
        .all()
    )


@router.post("/sync")
async def sync_products(
    account: models.WBAccount = Depends(get_owned_account),
    db: Session = Depends(get_db),
):
    if not account.api_key:
        raise HTTPException(400, "Account has no WB API key")
    account_id = account.id
    try:
        cards = await wb_content.fetch_all_cards(account.api_key)
    except wb_content.WBContentError as e:
        raise HTTPException(502, str(e))

    payload = []
    for c in cards:
        nm = c.get("nmID")
        if not nm:
            continue
        payload.append({
            "account_id": account_id,
            "nm_id": int(nm),
            "sa_name": c.get("vendorCode"),
            "title": (c.get("title") or "")[:512] or None,
            "brand": c.get("brand"),
            "subject_name": c.get("subjectName") or c.get("object"),
            "photo_url": wb_content.card_photo_url(c),
        })

    if payload:
        stmt = pg_insert(models.Product).values(payload)
        upd = {c.name: c for c in stmt.excluded if c.name not in ("id", "account_id", "nm_id")}
        stmt = stmt.on_conflict_do_update(constraint="uq_account_nm", set_=upd)
        db.execute(stmt)
        db.commit()

    return {"synced": len(payload)}
