from __future__ import annotations

import argparse
import tempfile
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from ultralytics import YOLO


def draw_boxes(
    image: np.ndarray, boxes, scores, classes, names, conf_threshold: float = 0.25
):
    h, w = image.shape[:2]
    for xyxy, conf, cls in zip(boxes, scores, classes):
        x1, y1, x2, y2 = map(int, xyxy)
        label = f"{names[int(cls)]} {conf:.2f}"
        color = (255, 0, 0)
        cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
        t_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)[0]
        cv2.rectangle(
            image, (x1, y1 - t_size[1] - 6), (x1 + t_size[0] + 6, y1), color, -1
        )
        cv2.putText(
            image,
            label,
            (x1 + 3, y1 - 4),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            1,
        )
    return image


def resolve_model_path(model_path: str) -> str:
    path = Path(model_path)
    if path.exists():
        return str(path)

    # Allow Ultralytics built-in model names like yolov8n.pt.
    if path.name == model_path and path.suffix == ".pt" and path.parent == Path("."):
        return model_path

    candidates = list(Path("runs").glob("**/weights/best.pt")) + list(
        Path("runs").glob("**/weights/last.pt")
    )
    if candidates:
        candidates.sort(key=lambda item: item.stat().st_mtime, reverse=True)
        chosen = candidates[0]
        print(f"Model not found: {model_path}")
        print(f"Using latest checkpoint instead: {chosen}")
        return str(chosen)

    raise FileNotFoundError(
        f"Model checkpoint not found: {model_path}. "
        "Train the model first or pass the correct checkpoint path."
    )


def normalize_source(source: str) -> str:
    source_path = Path(source)
    if not source_path.exists() or source_path.is_dir():
        return source

    supported_exts = {
        ".jpg",
        ".jpeg",
        ".png",
        ".bmp",
        ".webp",
        ".tif",
        ".tiff",
        ".gif",
        ".mp4",
        ".avi",
        ".mov",
        ".mkv",
        ".webm",
    }
    if source_path.suffix.lower() in supported_exts:
        return source

    temp_dir = Path(tempfile.gettempdir()) / "fruit_grade_detect"
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_path = temp_dir / f"{source_path.stem}.png"
    Image.open(source_path).convert("RGB").save(temp_path)
    print(f"Converted unsupported image format to: {temp_path}")
    return str(temp_path)


def run_inference(model_path: str, source: str, conf: float, iou: float, save_dir: str):
    resolved_model_path = resolve_model_path(model_path)
    model = YOLO(resolved_model_path)
    normalized_source = normalize_source(source)
    results = model.predict(source=normalized_source, conf=conf, iou=iou, imgsz=640)

    out_dir = Path(save_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for i, res in enumerate(results):
        # read original image
        img_path = Path(res.path) if hasattr(res, "path") else None
        if img_path and img_path.exists():
            img = cv2.imread(str(img_path))
        else:
            # fallback: get image from result
            img = res.orig_img

        boxes = res.boxes.xyxy.cpu().numpy() if len(res.boxes) else []
        scores = res.boxes.conf.cpu().numpy() if len(res.boxes) else []
        classes = res.boxes.cls.cpu().numpy() if len(res.boxes) else []

        if len(boxes):
            img = draw_boxes(img, boxes, scores, classes, model.names, conf)

        out_path = out_dir / f"det_{i}.jpg"
        cv2.imwrite(str(out_path), img)
        print(f"Saved: {out_path}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run YOLOv8 detection and save images with boxes"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="yolov8n.pt",
        help="Path to trained model or base model",
    )
    parser.add_argument(
        "--source", type=str, required=True, help="Image file, folder, or webcam (0)"
    )
    parser.add_argument("--conf", type=float, default=0.25)
    parser.add_argument("--iou", type=float, default=0.45)
    parser.add_argument("--save-dir", type=str, default="runs/detect")
    return parser.parse_args()


def main():
    args = parse_args()
    run_inference(args.model, args.source, args.conf, args.iou, args.save_dir)


if __name__ == "__main__":
    main()
