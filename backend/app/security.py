import os
from datetime import datetime, timedelta, timezone
import jwt
from argon2 import PasswordHasher
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from .db import get_db
from .models import User

SECRET = os.getenv("JWT_SECRET", "development-only-change-me")
hasher = PasswordHasher()
bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return hasher.verify(password_hash, password)
    except Exception:
        return False


def token_for(user: User) -> str:
    payload = {"sub": str(user.id), "exp": datetime.now(timezone.utc) + timedelta(hours=24)}
    return jwt.encode(payload, SECRET, algorithm="HS256")


def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
                 db: Session = Depends(get_db)) -> User:
    if not credentials:
        raise HTTPException(401, "Нужен вход в аккаунт")
    try:
        payload = jwt.decode(credentials.credentials, SECRET, algorithms=["HS256"])
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise HTTPException(401, "Сессия закончилась")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(401, "Аккаунт не найден")
    return user
