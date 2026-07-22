"""Auth endpoints — register, login, Google OAuth, refresh. Owner: Sumit"""
from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user
from auth.google_oauth import verify_google_token
from auth.schemas import (
    AccessTokenResponse,
    GoogleAuthRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserOut,
)
from auth.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from database.session import get_db
from models import User

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        email=body.email,
        name=body.name,
        password_hash=hash_password(body.password),
        auth_provider="email",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    invalid = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    user = db.query(User).filter(User.email == body.email).first()
    if user is None or user.password_hash is None:
        raise invalid
    if not verify_password(body.password, user.password_hash):
        raise invalid

    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post("/google", response_model=TokenResponse)
def google_auth(body: GoogleAuthRequest, db: Session = Depends(get_db)):
    try:
        payload = verify_google_token(body.id_token)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google token")

    email = payload["email"]
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        user = User(email=email, name=payload.get("name", email), auth_provider="google")
        db.add(user)
        db.commit()
        db.refresh(user)

    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post("/refresh", response_model=AccessTokenResponse)
def refresh(body: RefreshRequest):
    unauthorized = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")
    try:
        payload = decode_token(body.refresh_token)
    except JWTError:
        raise unauthorized
    if payload.get("type") != "refresh":
        raise unauthorized

    return AccessTokenResponse(access_token=create_access_token(payload["sub"]))


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user