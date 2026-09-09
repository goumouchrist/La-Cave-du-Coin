from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import client_ip
from app.schemas import LoginRequest, TokenResponse
from app.security import create_access_token
from app.services import users as users_service
from app.services import logs as logs_service

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = users_service.authenticate(db, payload.username, payload.password)
    if not user:
        logs_service.record(db, None, "login_failed", {"username": payload.username}, client_ip(request))
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Identifiant ou mot de passe incorrect")

    token = create_access_token(user.id, user.role.value)
    logs_service.record(db, user.id, "login_success", None, client_ip(request))
    return TokenResponse(access_token=token, role=user.role, user_id=user.id, username=user.username)
