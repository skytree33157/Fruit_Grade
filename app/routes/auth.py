"""Authentication routes for login and signup."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.auth import AuthCredentials, AuthResponse, UserProfile
from app.services.user_store import authenticate_user, get_current_user, register_user
from fastapi import Depends

router = APIRouter(prefix="/auth")


@router.post("/signup", response_model=AuthResponse)
async def signup(payload: AuthCredentials):
    try:
        return register_user(payload.username, payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/login", response_model=AuthResponse)
async def login(payload: AuthCredentials):
    try:
        return authenticate_user(payload.username, payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.get("/me", response_model=UserProfile)
async def me(user: dict = Depends(get_current_user)):
    return {
        "id": user["id"],
        "username": user["username"],
        "created_at": user["created_at"],
    }