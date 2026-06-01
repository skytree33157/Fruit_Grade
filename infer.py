from __future__ import annotations

import argparse
from pathlib import Path

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


@torch.no_grad()
def predict_image(
    image_path: str, checkpoint_path: str = "fruit_grade_resnet101.pth"
) -> dict:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    ckpt_path = Path(checkpoint_path)
    if not ckpt_path.exists():
        raise FileNotFoundError(f"Checkpoint not found: {ckpt_path}")

    image_file = Path(image_path)
    if not image_file.exists():
        raise FileNotFoundError(f"Image not found: {image_file}")

    ckpt = torch.load(ckpt_path, map_location=device)

    classes = ckpt["classes"]
    num_classes = ckpt["num_classes"]

    weights = models.ResNet101_Weights.DEFAULT
    model = models.resnet101(weights=None)
    model.fc = nn.Linear(model.fc.in_features, num_classes)
    model.load_state_dict(ckpt["weights"])
    model = model.to(device)
    model.eval()

    transform = weights.transforms()
    image = Image.open(image_file).convert("RGB")
    tensor = transform(image).unsqueeze(0).to(device)

    logits = model(tensor)
    probs = torch.softmax(logits, dim=1)
    conf, pred = torch.max(probs, dim=1)

    predicted_class = classes[pred.item()]
    fruit_name, grade, grade_label_kr = split_class_name(predicted_class)

    return {
        "predicted_class": predicted_class,
        "fruit_name": fruit_name,
        "grade": grade,
        "grade_label_kr": grade_label_kr,
        "confidence": float(conf.item()),
    }


def parse_args():
    parser = argparse.ArgumentParser(
        description="Infer fruit name and grade from one image"
    )
    parser.add_argument("--image", required=True, type=str, help="Input image path")
    parser.add_argument(
        "--checkpoint",
        default="fruit_grade_resnet101.pth",
        type=str,
        help="Trained checkpoint path",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    result = predict_image(args.image, args.checkpoint)

    print("=== Prediction Result ===")
    print(f"Predicted Class : {result['predicted_class']}")
    print(f"Fruit Name      : {result['fruit_name']}")
    print(f"Grade           : {result['grade']}")
    print(f"Grade (KR)      : {result['grade_label_kr']}")
    print(f"Confidence      : {result['confidence'] * 100:.2f}%")


if __name__ == "__main__":
    main()
