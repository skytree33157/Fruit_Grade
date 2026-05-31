"""Authentication schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AuthCredentials(BaseModel):
    username: str = Field(min_length=1, max_length=40)
    password: str = Field(min_length=1, max_length=128)


class UserProfile(BaseModel):
    id: str
    username: str
    created_at: str


class AuthResponse(BaseModel):
    token: str
    user: UserProfile