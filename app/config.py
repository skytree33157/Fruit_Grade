"""Application configuration helpers."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    YOLO_MODEL_PATH: str = os.getenv("YOLO_MODEL_PATH", "yolov8n.pt")
    CROP_CHECKPOINT: str = os.getenv("CROP_CHECKPOINT", "crop_classifier_resnet18.pth")
    RESNET_CHECKPOINT: str = os.getenv("RESNET_CHECKPOINT", "fruit_grade_resnet18.pth")
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini")
    LLM_API_KEY: str | None = os.getenv("LLM_API_KEY")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-2.5-flash")
    LLM_TIMEOUT: int = int(os.getenv("LLM_TIMEOUT", "10"))
    DEVICE: str | None = os.getenv("DEVICE")


settings = Settings()
