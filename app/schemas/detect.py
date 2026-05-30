"""Schemas for detection responses."""

from __future__ import annotations

from pydantic import BaseModel


class BBox(BaseModel):
    x: float
    y: float
    w: float
    h: float


class DetectedItem(BaseModel):
    id: int
    class_name: str
    score: float
    bbox: BBox


class DetectResponse(BaseModel):
    items: list[DetectedItem]
