"""Grade classification service."""

from __future__ import annotations

from app.config import settings
from app.services.resnet_model import ResNetPredictor

_classifier_instance: ResNetPredictor | None = None


def get_classifier() -> ResNetPredictor:
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = ResNetPredictor(settings.RESNET_CHECKPOINT)
    return _classifier_instance


def predict_grade(image_bytes: bytes) -> dict:
    result = get_classifier().predict_bytes(image_bytes)
    return {
        "class_name": result.predicted_class,
        "fruit_name": result.fruit_name,
        "grade": result.grade or "unknown",
        "grade_label_kr": result.grade_label_kr,
        "confidence": result.confidence,
    }
