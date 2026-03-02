from datetime import datetime, timedelta, timezone
from typing import Optional
import secrets

from fastapi import Depends, HTTPException, Request, Response, status
from jose import jwt, JWTError
import traceback
from core.config import GlobalSettings

SETTINGS = GlobalSettings()


JWT_ALGORITHM = "HS256"
JWT_SECRET_KEY = SETTINGS.JWT_SECRET_KEY

ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

ACCESS_COOKIE_NAME = "access_token"
REFRESH_COOKIE_NAME = "refresh_token"
CSRF_COOKIE_NAME = "csrf_token"

COOKIE_SECURE = False  # TODO: True in production (HTTPS)
COOKIE_SAMESITE = "lax"


def _create_token(data: dict, expires_delta: timedelta) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(tz=timezone.utc) + expires_delta
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_access_token(user_id: str) -> str:
    return _create_token(
        {"sub": user_id, "type": "access"},
        timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(user_id: str) -> str:
    return _create_token(
        {"sub": user_id, "type": "refresh"}, timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )


def verify_token(token: str, token_type: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != token_type:
            raise HTTPException(status_code=401, detail="Invalid token type")
        return payload
    # except JWTError:
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"{str(e)}, ::: {traceback.format_exc()}",
        )


def set_auth_cookies(response: Response, user_id: str):
    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)
    csrf_token = secrets.token_urlsafe(32)

    response.set_cookie(
        ACCESS_COOKIE_NAME,
        access_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    response.set_cookie(
        REFRESH_COOKIE_NAME,
        refresh_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )

    response.set_cookie(
        CSRF_COOKIE_NAME,
        csrf_token,
        httponly=False,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
    )


def clear_auth_cookies(response: Response):
    response.delete_cookie(ACCESS_COOKIE_NAME)
    response.delete_cookie(REFRESH_COOKIE_NAME)
    response.delete_cookie(CSRF_COOKIE_NAME)


def get_current_user(request: Request) -> str:
    token = request.cookies.get(ACCESS_COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    payload = verify_token(token, "access")
    return payload["sub"]


def get_optional_user(request: Request) -> str | None:
    token = request.cookies.get("access_token")
    if not token:
        return None

    try:
        payload = verify_token(token, "access")
        return payload["sub"]
    except Exception:
        return None


def csrf_protect(request: Request):
    csrf_cookie = request.cookies.get(CSRF_COOKIE_NAME)
    csrf_header = request.headers.get("X-CSRF-Token")

    if not csrf_cookie or not csrf_header:
        raise HTTPException(status_code=403, detail="CSRF token missing")

    if not secrets.compare_digest(csrf_cookie, csrf_header):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")


def refresh_access_token(request: Request, response: Response):
    refresh_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Missing refresh token")

    payload = verify_token(refresh_token, "refresh")
    user_id = payload["sub"]

    new_access_token = create_access_token(user_id)

    response.set_cookie(
        ACCESS_COOKIE_NAME,
        new_access_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
