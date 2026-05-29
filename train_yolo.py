from __future__ import annotations

import argparse
from pathlib import Path

from ultralytics import YOLO


def parse_args():
    parser = argparse.ArgumentParser(
        description="Train YOLOv8 on Roboflow/YOLO segmentation dataset"
    )
    parser.add_argument(
        "--data", type=str, default="first/data.yaml", help="Path to data.yaml"
    )
    parser.add_argument(
        "--model", type=str, default="yolov8n-seg.pt", help="Base model or checkpoint"
    )
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--project", type=str, default="runs/train")
    parser.add_argument("--name", type=str, default="exp")
    parser.add_argument(
        "--task",
        type=str,
        default="segment",
        choices=["segment", "detect"],
        help="Ultralytics task type",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    data_path = Path(args.data)
    if not data_path.exists():
        raise FileNotFoundError(f"data.yaml not found: {data_path}")

    model = YOLO(args.model)
    model.train(
        data=str(data_path),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        project=args.project,
        name=args.name,
        task=args.task,
    )


if __name__ == "__main__":
    main()
