"""YOLO detection service with a safe mock fallback."""

from __future__ import annotations

from typing import Dict, List

from app.config import settings


class BaseDetector:
    def predict(self, image_bytes: bytes) -> List[Dict]:
        raise NotImplementedError


_detector_instance: BaseDetector | None = None


def get_detector() -> BaseDetector:
    global _detector_instance
    if _detector_instance is None:
        try:
            import cv2
            import numpy as np
            from ultralytics import YOLO

            model = YOLO(settings.YOLO_MODEL_PATH)

            class YOLODetector(BaseDetector):
                def __init__(self, model):
                    self.model = model

                def predict(self, image_bytes: bytes):
                    arr = np.frombuffer(image_bytes, np.uint8)
                    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                    results = self.model.predict(source=img, imgsz=640, conf=0.25)
                    items = []
                    for result in results:
                        boxes = result.boxes
                        if boxes is None:
                            continue
                        names = getattr(result, "names", self.model.names)
                        for index, box in enumerate(boxes.xyxy.cpu().numpy()):
                            conf = (
                                float(boxes.conf[index].cpu().numpy())
                                if hasattr(boxes, "conf")
                                else 0.0
                            )
                            cls = (
                                int(boxes.cls[index].cpu().numpy())
                                if hasattr(boxes, "cls")
                                else 0
                            )
                            x1, y1, x2, y2 = box
                            items.append(
                                {
                                    "id": index,
                                    "class_name": (
                                        names.get(cls, str(cls))
                                        if hasattr(names, "get")
                                        else str(cls)
                                    ),
                                    "score": conf,
                                    "bbox": {
                                        "x": float(x1),
                                        "y": float(y1),
                                        "w": float(x2 - x1),
                                        "h": float(y2 - y1),
                                    },
                                }
                            )
                    return items

            _detector_instance = YOLODetector(model)
        except Exception:

            class MockDetector(BaseDetector):
                def predict(self, image_bytes: bytes):
                    return []

            _detector_instance = MockDetector()
    return _detector_instance
