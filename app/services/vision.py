"""End-to-end image analysis pipeline."""

from __future__ import annotations

import cv2
import numpy as np

from app.services.classifier import predict_grade
from app.services.crop_classifier import predict_crop_name
from app.services.detector import get_detector
from app.services.resnet_model import clamp_bbox
import re


def _decode_bgr(image_bytes: bytes):
    array = np.frombuffer(image_bytes, np.uint8)
    bgr = cv2.imdecode(array, cv2.IMREAD_COLOR)
    if bgr is None:
        raise ValueError("Failed to decode image bytes")
    return bgr


class VisionPipeline:
    def detect(self, image_bytes: bytes):
        return get_detector().predict(image_bytes)

    def analyze(self, image_bytes: bytes) -> list[dict]:
        detector = get_detector()
        detections = detector.predict(image_bytes)
        bgr_image = _decode_bgr(image_bytes)
        height, width = bgr_image.shape[:2]

        results: list[dict] = []
        def _normalize_name(name: str | None) -> str | None:
            if not name:
                return name
            s = str(name).lower()
            s = s.replace("-", "_")
            s = s.replace(" ", "_")
            s = re.sub(r"[^a-z0-9_]", "", s)
            return s

        for detection in detections:
            bbox = detection["bbox"]
            x1, y1, x2, y2 = clamp_bbox(
                int(bbox["x"]),
                int(bbox["y"]),
                int(bbox["x"] + bbox["w"]),
                int(bbox["y"] + bbox["h"]),
                width,
                height,
            )
            crop = bgr_image[y1:y2, x1:x2]
            crop_bytes = self._encode_crop(crop)
            crop_pred = predict_crop_name(crop_bytes)
            grade_pred = predict_grade(crop_bytes)
            results.append(
                {
                    "id": detection["id"],
                    "bbox": detection["bbox"],
                    "detector_class_name": _normalize_name(detection["class_name"]),
                    "detector_confidence": detection["score"],
                    "crop_name": _normalize_name(crop_pred.get("crop_name")),
                    "crop_class_name": _normalize_name(crop_pred.get("predicted_class")),
                    "crop_confidence": crop_pred["confidence"],
                    "class_name": grade_pred["fruit_name"],
                    "grade": grade_pred["grade"],
                    "grade_label_kr": grade_pred["grade_label_kr"],
                    "grade_confidence": grade_pred["confidence"],
                }
            )
        return results

    @staticmethod
    def _encode_crop(crop_bgr) -> bytes:
        ok, encoded = cv2.imencode(".jpg", crop_bgr)
        if not ok:
            raise ValueError("Failed to encode crop image")
        return encoded.tobytes()


_vision_pipeline: VisionPipeline | None = None


def get_vision_pipeline() -> VisionPipeline:
    global _vision_pipeline
    if _vision_pipeline is None:
        _vision_pipeline = VisionPipeline()
    return _vision_pipeline
