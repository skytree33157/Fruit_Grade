"""Combined analyze route for multi-object inference."""

from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas.analyze import AnalyzeResponse
from app.services import vision as vision_service

router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(image: UploadFile = File(...)):
    if image.content_type not in ("image/jpeg", "image/png"):
        raise HTTPException(status_code=400, detail="Invalid image type")
    data = await image.read()
    return {"items": vision_service.get_vision_pipeline().analyze(data)}
