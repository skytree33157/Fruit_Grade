"""Schemas for recipe requests and responses."""

from __future__ import annotations

from pydantic import BaseModel


class RecipeRequest(BaseModel):
    ingredient: str


class RecipeResponse(BaseModel):
    title: str
    ingredients: list[str]
    steps: list[str]
