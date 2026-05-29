from __future__ import annotations

import argparse
import ast
import random
from pathlib import Path
from typing import List, Tuple

import torch
import torch.nn as nn
import torch.optim as optim
from PIL import Image
from sklearn.metrics import f1_score, precision_score, recall_score
from torch.utils.data import DataLoader, Dataset
from torchvision import models
import re


def load_data_yaml(data_yaml: Path) -> dict:
    text = data_yaml.read_text(encoding="utf-8")
    result: dict = {}
    for line in text.splitlines():
        if line.strip().startswith("train:"):
            result["train"] = line.split("train:", 1)[1].strip()
        elif line.strip().startswith("val:") or line.strip().startswith("validation:"):
            result["val"] = line.split("val:", 1)[1].strip()
        elif line.strip().startswith("test:"):
            result["test"] = line.split("test:", 1)[1].strip()
        elif line.strip().startswith("names:"):
            names_part = line.split("names:", 1)[1].strip()
            try:
                result["names"] = ast.literal_eval(names_part)
            except Exception:
                # fallback: try to parse bracketed part across multiple lines
                start = text.find("names:")
                names_text = text[start + len("names:") :].strip()
                # crude: find first closing bracket
                end = names_text.find("]")
                if end != -1:
                    result["names"] = ast.literal_eval(names_text[: end + 1])
    return result


class ImagePathDataset(Dataset):
    def __init__(self, files: List[Path], labels: List[int], transform):
        self.files = files
        self.labels = labels
        self.transform = transform

    def __len__(self):
        return len(self.files)

    def __getitem__(self, idx: int):
        path = self.files[idx]
        image = Image.open(path).convert("RGB")
        image = self.transform(image)
        label = self.labels[idx]
        return image, label


def infer_label_from_filename(fname: str, classes: List[str]) -> Tuple[str, int] | None:
    name_lower = fname.lower()
    for cls in classes:
        cls_norm = cls.lower()
        alternatives = {cls_norm, cls_norm.replace("-", "_"), cls_norm.replace("_", "-")}
        for alt in alternatives:
            if alt in name_lower:
                return cls, classes.index(cls)
    return None


def strip_grade_suffix(name: str) -> str:
    """Remove common grade suffix patterns from class names (e.g. `_L_1-10`, `_1`, `-1`)."""
    if not name:
        return name
    s = name
    # normalize spacing
    s = s.strip()
    # remove patterns like '_L_1-10', '_L', '_1-10', '-1-10', '_123'
    s = re.sub(r'([_-]L[_\d\-].*$)|([_-]L$)|([_-]\d+.*$)', '', s, flags=re.IGNORECASE)
    return s


@torch.no_grad()
def evaluate(model, loader, criterion, device):
    model.eval()
    total_loss = 0.0
    total = 0
    correct = 0
    true_labels: list[int] = []
    pred_labels: list[int] = []

    for inputs, labels in loader:
        inputs = inputs.to(device)
        labels = labels.to(device)

        outputs = model(inputs)
        loss = criterion(outputs, labels)

        total_loss += loss.item() * inputs.size(0)
        _, predicted = torch.max(outputs, 1)
        total += labels.size(0)
        correct += (predicted == labels).sum().item()

        true_labels.extend(labels.cpu().tolist())
        pred_labels.extend(predicted.cpu().tolist())

    avg_loss = total_loss / max(total, 1)
    acc = correct / max(total, 1)
    precision = precision_score(true_labels, pred_labels, average="macro", zero_division=0)
    recall = recall_score(true_labels, pred_labels, average="macro", zero_division=0)
    f1 = f1_score(true_labels, pred_labels, average="macro", zero_division=0)
    return avg_loss, acc, precision, recall, f1


def train(args):
    torch.manual_seed(args.seed)
    random.seed(args.seed)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    data_root = Path(args.data_root)
    # locate data.yaml
    data_yaml = data_root / "data.yaml"
    if not data_yaml.exists():
        # maybe user passed folder that contains data.yaml (e.g., 'first')
        raise FileNotFoundError(f"Could not find data.yaml at: {data_yaml}")

    meta = load_data_yaml(data_yaml)
    classes = meta.get("names")
    if not classes:
        raise RuntimeError("Could not parse class names from data.yaml")

    # strip grade suffixes from class names and deduplicate while preserving order
    cleaned: list[str] = []
    seen = set()
    for c in classes:
        c_clean = strip_grade_suffix(c).strip()
        if c_clean not in seen:
            seen.add(c_clean)
            cleaned.append(c_clean)
    classes = cleaned

    # locate train/val image folders
    train_dir = data_root / "train" / "images"
    val_dir = data_root / "valid" / "images"
    if not train_dir.exists():
        # try alternative path from data.yaml
        train_rel = meta.get("train")
        if train_rel:
            train_dir = (data_yaml.parent / train_rel).resolve()
    if not val_dir.exists():
        val_rel = meta.get("val")
        if val_rel:
            val_dir = (data_yaml.parent / val_rel).resolve()

    if not train_dir.exists() or not val_dir.exists():
        raise FileNotFoundError(f"Train/val images not found: {train_dir} / {val_dir}")

    # index images and infer labels by filename
    allowed = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    train_files: list[Path] = []
    train_labels: list[int] = []
    skipped = 0

    for p in sorted(train_dir.iterdir()):
        if p.suffix.lower() not in allowed:
            continue
        res = infer_label_from_filename(p.name, classes)
        if res is None:
            skipped += 1
            continue
        _, label = res
        train_files.append(p)
        train_labels.append(label)

    val_files: list[Path] = []
    val_labels: list[int] = []
    for p in sorted(val_dir.iterdir()):
        if p.suffix.lower() not in allowed:
            continue
        res = infer_label_from_filename(p.name, classes)
        if res is None:
            skipped += 1
            continue
        _, label = res
        val_files.append(p)
        val_labels.append(label)

    if not train_files:
        raise RuntimeError(f"No training images indexed in {train_dir}")

    print(f"Indexed {len(train_files)} train images, {len(val_files)} val images, skipped {skipped} files")

    weights = models.ResNet18_Weights.DEFAULT
    model = models.resnet18(weights=weights)
    preprocess = weights.transforms()

    num_classes = len(classes)
    num_features = model.fc.in_features
    model.fc = nn.Linear(num_features, num_classes)
    model = model.to(device)

    train_dataset = ImagePathDataset(train_files, train_labels, transform=preprocess)
    val_dataset = ImagePathDataset(val_files, val_labels, transform=preprocess)

    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.num_workers,
        pin_memory=torch.cuda.is_available(),
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        pin_memory=torch.cuda.is_available(),
    )

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=args.lr)

    best_val_acc = 0.0
    save_path = Path(args.save_path)

    for epoch in range(args.epochs):
        model.train()
        running_loss = 0.0
        total = 0
        correct = 0

        for inputs, labels in train_loader:
            inputs = inputs.to(device)
            labels = labels.to(device)

            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * inputs.size(0)
            _, predicted = torch.max(outputs, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

        train_loss = running_loss / max(total, 1)
        train_acc = correct / max(total, 1)

        val_loss, val_acc, val_precision, val_recall, val_f1 = evaluate(
            model, val_loader, criterion, device
        )

        print(
            f"Epoch {epoch+1}/{args.epochs} | Train Loss: {train_loss:.4f}, Train Acc: {train_acc*100:.2f}% | "
            f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc*100:.2f}%"
        )
        print(f"Val Precision: {val_precision*100:.2f}% | Val Recall: {val_recall*100:.2f}% | Val F1: {val_f1*100:.2f}%")

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            checkpoint = {
                "weights": model.state_dict(),
                "classes": classes,
                "class_to_idx": {name: i for i, name in enumerate(classes)},
                "num_classes": num_classes,
                "model_name": "resnet18",
                "best_val_acc": best_val_acc,
                "image_transform": "ResNet18_Weights.DEFAULT.transforms()",
            }
            torch.save(checkpoint, save_path)
            print(f"Best model saved to: {save_path} (Val Acc: {best_val_acc*100:.2f}%)")

    print("Training done")


def parse_args():
    parser = argparse.ArgumentParser(description="Train crop classifier using first/ dataset")
    parser.add_argument("--data-root", type=str, default="first", help="Path to dataset root (contains data.yaml, train/, valid/)")
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--save-path", type=str, default="crop_classifier_resnet18.pth")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    train(args)
