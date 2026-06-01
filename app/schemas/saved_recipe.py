"""Schemas for persisted saved recipes."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class SavedRecipeCreate(BaseModel):
    ingredient: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=200)
    ingredients: list[str]
    steps: list[str]
    created_at: datetime | None = None
    checklist_checked: list[bool] | None = None


class SavedRecipeChecklistUpdate(BaseModel):
    checklist_checked: list[bool]


class SavedRecipeResponse(BaseModel):
    id: str
    ingredient: str
    title: str
    ingredients: list[str]
    steps: list[str]
    created_at: datetime
    checklist_checked: list[bool]