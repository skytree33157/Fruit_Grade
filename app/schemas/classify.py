"""Schemas for grade classification responses."""

from __future__ import annotations

from pydantic import BaseModel


class ClassifyResponse(BaseModel):
    class_name: str
    grade: str
    confidence: float
    low_confidence: bool = False
