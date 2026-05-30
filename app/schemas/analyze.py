"""Schemas for combined detection + classification output."""

from __future__ import annotations

from pydantic import BaseModel


class AnalyzeBBox(BaseModel):
    x: float
    y: float
    w: float
    h: float


class AnalyzeItem(BaseModel):
    id: int
    bbox: AnalyzeBBox
    detector_class_name: str
    detector_confidence: float
    crop_name: str
    crop_class_name: str
    crop_confidence: float
    class_name: str
    grade: str | None = None
    grade_label_kr: str | None = None
    grade_confidence: float


class AnalyzeResponse(BaseModel):
    items: list[AnalyzeItem]
