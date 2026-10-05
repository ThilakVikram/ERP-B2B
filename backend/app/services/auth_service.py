"""Signup / login business logic."""

import re

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config import ACCESS_TOKEN_EXPIRE_MINUTES, REMEMBER_ME_EXPIRE_MINUTES
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories import user_repository
from app.schemas.auth import LoginRequest, SignupRequest, TokenResponse
from app.schemas.user import UserOut


def _generate_username(db: Session, email: str) -> str:
    """Derive a unique username from the email's local part (john.doe -> john.doe, john.doe1, ...)."""
    base = re.sub(r"[^a-z0-9._-]", "", email.split("@")[0].lower())[:90] or "user"
    username, n = base, 0
    while user_repository.username_exists(db, username):
        n += 1
        username = f"{base}{n}"
    return username


def _token_response(user: User, expires_minutes: int) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(user.id, expires_minutes),
        expires_in=expires_minutes * 60,
        user=UserOut.model_validate(user),
    )


def signup(db: Session, data: SignupRequest) -> TokenResponse:
    email = data.email.lower()
    if user_repository.get_by_email(db, email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    user = user_repository.create(
        db,
        email=email,
        username=_generate_username(db, email),
        first_name=data.first_name.strip(),
        last_name=data.last_name.strip(),
        hashed_password=hash_password(data.password),
    )
    return _token_response(user, ACCESS_TOKEN_EXPIRE_MINUTES)


def login(db: Session, data: LoginRequest) -> TokenResponse:
    user = user_repository.get_by_email(db, data.email.lower())
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is disabled",
        )

    expires = REMEMBER_ME_EXPIRE_MINUTES if data.remember_me else ACCESS_TOKEN_EXPIRE_MINUTES
    return _token_response(user, expires)
