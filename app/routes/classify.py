"""Classification API routes."""

from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas.classify import ClassifyResponse
from app.services import classifier as classifier_service

router = APIRouter()


@router.post("/classify", response_model=ClassifyResponse)
async def classify(image: UploadFile = File(...)):
    if image.content_type not in ("image/jpeg", "image/png"):
        raise HTTPException(status_code=400, detail="Invalid image type")
    data = await image.read()
    classifier = classifier_service.get_classifier()
    pred = classifier.predict(data)
    low_conf = pred.get("confidence", 0) < 0.4
    return {
        "class_name": pred.get("class_name", "unknown"),
        "grade": pred.get("grade", "unknown"),
        "confidence": float(pred.get("confidence", 0.0)),
        "low_confidence": low_conf,
    }
