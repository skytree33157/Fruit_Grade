"""Shared ResNet18 checkpoint loading and inference helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from torchvision import models

GRADE_LABEL_MAP = {
    "S": "하",
    "M": "중",
    "L": "상",
}


def split_class_name(class_name: str) -> tuple[str, str | None, str | None]:
    parts = class_name.split("_")
    if len(parts) < 2:
        return class_name, None, None

    maybe_grade = parts[-1]
    if maybe_grade in GRADE_LABEL_MAP:
        fruit_name = "_".join(parts[:-1])
        return fruit_name, maybe_grade, GRADE_LABEL_MAP[maybe_grade]

    return class_name, None, None


def decode_image_bytes(image_bytes: bytes) -> Image.Image:
    array = np.frombuffer(image_bytes, np.uint8)
    bgr = cv2.imdecode(array, cv2.IMREAD_COLOR)
    if bgr is None:
        raise ValueError("Failed to decode image bytes")
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    return Image.fromarray(rgb)


def clamp_bbox(
    x1: int, y1: int, x2: int, y2: int, width: int, height: int
) -> tuple[int, int, int, int]:
    left = max(0, min(x1, width - 1))
    top = max(0, min(y1, height - 1))
    right = max(left + 1, min(x2, width))
    bottom = max(top + 1, min(y2, height))
    return left, top, right, bottom


@dataclass
class ResNetPrediction:
    predicted_class: str
    fruit_name: str
    grade: str | None
    grade_label_kr: str | None
    confidence: float


class ResNetPredictor:
    def __init__(self, checkpoint_path: str) -> None:
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        ckpt_path = Path(checkpoint_path)
        if not ckpt_path.exists():
            raise FileNotFoundError(f"Checkpoint not found: {ckpt_path}")

        ckpt = torch.load(ckpt_path, map_location=self.device)
        self.classes = ckpt["classes"]
        num_classes = ckpt["num_classes"]

        self.weights = models.ResNet101_Weights.DEFAULT
        self.transform = self.weights.transforms()

        self.model = models.resnet101(weights=None)
        self.model.fc = nn.Linear(self.model.fc.in_features, num_classes)
        self.model.load_state_dict(ckpt["weights"])
        self.model = self.model.to(self.device)
        self.model.eval()

    @torch.no_grad()
    def predict_pil(self, image: Image.Image) -> ResNetPrediction:
        tensor = self.transform(image.convert("RGB")).unsqueeze(0).to(self.device)

        logits = self.model(tensor)
        probs = torch.softmax(logits, dim=1)
        conf, pred = torch.max(probs, dim=1)

        predicted_class = self.classes[pred.item()]
        fruit_name, grade, grade_label_kr = split_class_name(predicted_class)

        return ResNetPrediction(
            predicted_class=predicted_class,
            fruit_name=fruit_name,
            grade=grade,
            grade_label_kr=grade_label_kr,
            confidence=float(conf.item()),
        )

    @torch.no_grad()
    def predict(self, image_bytes: bytes) -> ResNetPrediction:
        return self.predict_bytes(image_bytes)

    @torch.no_grad()
    def predict_bytes(self, image_bytes: bytes) -> ResNetPrediction:
        return self.predict_pil(decode_image_bytes(image_bytes))

    @torch.no_grad()
    def predict_bgr(self, bgr_image) -> ResNetPrediction:
        rgb_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)
        return self.predict_pil(Image.fromarray(rgb_image))
