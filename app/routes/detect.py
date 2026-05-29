"""Detection API routes."""

from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas.detect import DetectResponse
from app.services import detector as detector_service

router = APIRouter()


@router.post("/detect", response_model=DetectResponse)
async def detect(image: UploadFile = File(...)):
    if image.content_type not in ("image/jpeg", "image/png"):
        raise HTTPException(status_code=400, detail="Invalid image type")
    data = await image.read()
    detector = detector_service.get_detector()
    return {"items": detector.predict(data)}
