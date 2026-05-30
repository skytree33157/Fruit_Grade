"""Crop species classifier service."""

from __future__ import annotations

from app.config import settings
from app.services.resnet_model import ResNetPredictor, split_class_name

_crop_classifier_instance: ResNetPredictor | None = None


def get_crop_classifier() -> ResNetPredictor:
    global _crop_classifier_instance
    if _crop_classifier_instance is None:
        _crop_classifier_instance = ResNetPredictor(settings.CROP_CHECKPOINT)
    return _crop_classifier_instance


def predict_crop_name(image_bytes: bytes) -> dict:
    predictor = get_crop_classifier()
    result = predictor.predict_bytes(image_bytes)
    crop_name, _, _ = split_class_name(result.predicted_class)
    return {
        "predicted_class": result.predicted_class,
        "crop_name": crop_name,
        "confidence": result.confidence,
    }
