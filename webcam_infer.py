from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import torch
import torch.nn as nn
from PIL import Image
from torchvision import models

GRADE_LABEL_MAP = {"S": "하", "M": "중", "L": "상"}


def split_class_name(class_name: str) -> tuple[str, str | None, str | None]:
    parts = class_name.split("_")
    if len(parts) < 2:
        return class_name, None, None

    maybe_grade = parts[-1]
    if maybe_grade in GRADE_LABEL_MAP:
        fruit_name = "_".join(parts[:-1])
        return fruit_name, maybe_grade, GRADE_LABEL_MAP[maybe_grade]

    return class_name, None, None


class FruitGradePredictor:
    def __init__(self, checkpoint_path: str) -> None:
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        ckpt_path = Path(checkpoint_path)
        if not ckpt_path.exists():
            raise FileNotFoundError(f"Checkpoint not found: {ckpt_path}")

        ckpt = torch.load(ckpt_path, map_location=self.device)
        self.classes = ckpt["classes"]
        num_classes = ckpt["num_classes"]

        self.weights = models.ResNet18_Weights.DEFAULT
        self.transform = self.weights.transforms()

        self.model = models.resnet18(weights=None)
        self.model.fc = nn.Linear(self.model.fc.in_features, num_classes)
        self.model.load_state_dict(ckpt["weights"])
        self.model = self.model.to(self.device)
        self.model.eval()

    @torch.no_grad()
    def predict_frame(self, bgr_frame):
        rgb_frame = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(rgb_frame)
        tensor = self.transform(image).unsqueeze(0).to(self.device)

        logits = self.model(tensor)
        probs = torch.softmax(logits, dim=1)
        conf, pred = torch.max(probs, dim=1)

        predicted_class = self.classes[pred.item()]
        fruit_name, grade, grade_label_kr = split_class_name(predicted_class)

        return {
            "predicted_class": predicted_class,
            "fruit_name": fruit_name,
            "grade": grade,
            "grade_label_kr": grade_label_kr,
            "confidence": float(conf.item()),
        }


def draw_result(frame, result: dict, fps: float | None = None):
    lines = [
        f"Class: {result['predicted_class']}",
        f"Fruit: {result['fruit_name']}",
        f"Grade: {result['grade']} ({result['grade_label_kr']})",
        f"Confidence: {result['confidence'] * 100:.2f}%",
        "Press Q to quit",
    ]
    if fps is not None:
        lines.insert(0, f"FPS: {fps:.1f}")

    y = 30
    for text in lines:
        cv2.putText(
            frame,
            text,
            (20, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (30, 255, 30),
            2,
            cv2.LINE_AA,
        )
        y += 30


def parse_args():
    parser = argparse.ArgumentParser(
        description="Real-time fruit grade inference from webcam"
    )
    parser.add_argument(
        "--checkpoint",
        type=str,
        default="fruit_grade_resnet18.pth",
        help="Model checkpoint path",
    )
    parser.add_argument(
        "--camera-id", type=int, default=0, help="Webcam index (default: 0)"
    )
    parser.add_argument("--width", type=int, default=1280, help="Capture width")
    parser.add_argument("--height", type=int, default=720, help="Capture height")
    parser.add_argument(
        "--infer-every", type=int, default=3, help="Run model every N frames for speed"
    )
    return parser.parse_args()


def main():
    args = parse_args()

    predictor = FruitGradePredictor(args.checkpoint)

    cap = cv2.VideoCapture(args.camera_id)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)

    if not cap.isOpened():
        raise RuntimeError(
            "Cannot open webcam. Check --camera-id or camera permissions."
        )

    print("Webcam started. Press Q to quit.")

    frame_idx = 0
    last_result = None
    prev_tick = cv2.getTickCount()

    while True:
        ok, frame = cap.read()
        if not ok:
            print("Frame read failed. Exiting.")
            break

        if frame_idx % max(args.infer_every, 1) == 0:
            last_result = predictor.predict_frame(frame)

        curr_tick = cv2.getTickCount()
        fps = (
            cv2.getTickFrequency() / (curr_tick - prev_tick)
            if curr_tick != prev_tick
            else 0.0
        )
        prev_tick = curr_tick

        if last_result is not None:
            draw_result(frame, last_result, fps=fps)

        cv2.imshow("Fruit Grade Classifier", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break

        frame_idx += 1

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
