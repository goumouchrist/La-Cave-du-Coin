from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import client_ip, get_current_user
from app.models import CashSession, User
from app.schemas import CashSessionClose, CashSessionOpen, CashSessionOut, CashSessionSummary
from app.services import cash as cash_service
from app.services import logs as logs_service

router = APIRouter(prefix="/api/cash-sessions", tags=["cash"])


@router.get("", response_model=list[CashSessionOut])
def list_sessions(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(CashSession).order_by(CashSession.opened_at.desc()).all()


@router.post("/open", response_model=CashSessionOut, status_code=status.HTTP_201_CREATED)
def open_session(
    payload: CashSessionOpen,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        session_ = cash_service.open_session(db, current_user.id, payload.opening_amount)
    except cash_service.SessionAlreadyOpenError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))

    logs_service.record(db, current_user.id, "cash_session_opened", {"session_id": session_.id}, client_ip(request))
    return session_


@router.post("/{session_id}/close", response_model=CashSessionOut)
def close_session(
    session_id: int,
    payload: CashSessionClose,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session_ = db.get(CashSession, session_id)
    if not session_:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session introuvable")

    try:
        session_ = cash_service.close_session(db, session_, current_user.id, payload.closing_physical)
    except cash_service.SessionNotOpenError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))

    action = "cash_session_blocked" if session_.status.value == "blocked" else "cash_session_closed"
    logs_service.record(db, current_user.id, action, {"session_id": session_.id, "gap": session_.gap_amount}, client_ip(request))
    return session_


@router.get("/current", response_model=CashSessionOut | None)
def get_current_session(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    from app.models import CashSessionStatus

    return db.query(CashSession).filter(CashSession.status == CashSessionStatus.OPEN).first()


@router.get("/{session_id}/summary", response_model=CashSessionSummary)
def get_session_summary(session_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    session_ = db.get(CashSession, session_id)
    if not session_:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session introuvable")
    return cash_service.compute_summary(db, session_)
