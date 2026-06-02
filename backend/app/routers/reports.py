import time
from datetime import date

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from .. import models, schemas
from ..db import get_db
from ..deps import current_user, get_owned_account
from ..services import excel_parser, ingest, wb_api

router = APIRouter(prefix="/reports", tags=["reports"])

_PULL_COOLDOWN_S = 65
_last_pull: dict[int, float] = {}


@router.get("", response_model=list[schemas.ReportOut])
def list_reports(
    account_id: int | None = None,
    db: Session = Depends(get_db),
    user: models.User = Depends(current_user),
):
    q = db.query(models.Report).join(models.WBAccount).filter(models.WBAccount.user_id == user.id)
    if account_id:
        q = q.filter(models.Report.account_id == account_id)
    return q.order_by(models.Report.created_at.desc()).all()


@router.delete("/{report_id}", status_code=204)
def delete_report(
    report_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(current_user),
):
    r = db.get(models.Report, report_id)
    if not r:
        raise HTTPException(404)
    acc = db.get(models.WBAccount, r.account_id)
    if not acc or acc.user_id != user.id:
        raise HTTPException(404)
    db.delete(r); db.commit()


@router.post("/pull", response_model=schemas.ReportOut)
async def pull_from_api(
    data: schemas.ApiPullIn,
    db: Session = Depends(get_db),
    user: models.User = Depends(current_user),
):
    account = db.get(models.WBAccount, data.account_id)
    if not account or account.user_id != user.id:
        raise HTTPException(404, "Account not found")
    if not account.api_key:
        raise HTTPException(400, "Account has no WB API key")

    now = time.monotonic()
    last = _last_pull.get(account.id, 0)
    elapsed = now - last
    if elapsed < _PULL_COOLDOWN_S:
        wait = int(_PULL_COOLDOWN_S - elapsed)
        raise HTTPException(429, f"Подождите {wait} сек: лимит WB API 1 запрос в минуту.")
    _last_pull[account.id] = now

    try:
        rows = await wb_api.fetch_report_detail(account.api_key, data.date_from, data.date_to)
    except wb_api.WBRateLimitError as e:
        raise HTTPException(429, str(e))
    except wb_api.WBApiError as e:
        raise HTTPException(502, str(e))
    report = ingest.ingest_rows(db, account.id, "api", data.date_from, data.date_to, rows)
    return report


@router.post("/upload", response_model=schemas.ReportOut)
async def upload_excel(
    account_id: int = Form(...),
    date_from: date = Form(...),
    date_to: date = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: models.User = Depends(current_user),
):
    account = db.get(models.WBAccount, account_id)
    if not account or account.user_id != user.id:
        raise HTTPException(404, "Account not found")
    content = await file.read()
    try:
        rows = excel_parser.parse_report_excel(content)
    except Exception as e:
        raise HTTPException(400, f"Failed to parse Excel: {e}")
    report = ingest.ingest_rows(db, account.id, "excel", date_from, date_to, rows)
    return report
