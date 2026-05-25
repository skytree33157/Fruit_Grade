from __future__ import annotations

import argparse
import random
import zipfile
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

import torch
import torch.nn as nn
import torch.optim as optim
from PIL import Image
from sklearn.metrics import f1_score, precision_score, recall_score
from torch.utils.data import DataLoader, Dataset
from torchvision import models


@dataclass(frozen=True)
class ZipSample:
    zip_path: Path
    inner_path: str
    class_name: str


GRADE_LABEL_MAP = {
    "S": "하",
    "M": "중",
    "L": "상"
}


def split_class_name(class_name: str) -> tuple[str, str | None, str | None]:
    # 기본 포맷 예: Apple_fuji_L -> fruit_name=Apple_fuji, grade=L
    parts = class_name.split("_")
    if len(parts) < 2:
        return class_name, None, None

    maybe_grade = parts[-1]
    if maybe_grade in GRADE_LABEL_MAP:
        fruit_name = "_".join(parts[:-1])
        return fruit_name, maybe_grade, GRADE_LABEL_MAP[maybe_grade]

    return class_name, None, None


def infer_class_name_from_zip(zip_path: Path) -> str:
    # 파일명 예: Apple_fuji_L.zip -> class: Apple_fuji_L
    stem = zip_path.stem
    return stem


def discover_zip_samples(source_dir: Path) -> list[ZipSample]:
    allowed_exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    zip_files = sorted(source_dir.glob("*.zip"))
    samples: list[ZipSample] = []
    skipped_files: list[tuple[str, str]] = []

    for zf in zip_files:
        if zf.stat().st_size == 0:
            skipped_files.append((zf.name, "empty file"))
            continue

        class_name = infer_class_name_from_zip(zf)
        try:
            with zipfile.ZipFile(zf) as archive:
                for member in archive.namelist():
                    member_lower = member.lower()
                    if member_lower.endswith("/"):
                        continue
                    if any(member_lower.endswith(ext) for ext in allowed_exts):
                        samples.append(ZipSample(zip_path=zf, inner_path=member, class_name=class_name))
        except (zipfile.BadZipFile, OSError) as exc:
            skipped_files.append((zf.name, str(exc)))
            continue

    if not samples:
        raise RuntimeError(f"No image files found in zipped data: {source_dir}")

    if skipped_files:
        print(f"Warning: skipped {len(skipped_files)} invalid zip file(s) in {source_dir}")
        preview_count = min(10, len(skipped_files))
        for file_name, reason in skipped_files[:preview_count]:
            print(f" - {file_name}: {reason}")
        if len(skipped_files) > preview_count:
            print(f" - ... and {len(skipped_files) - preview_count} more")

    return samples


class FruitZipDataset(Dataset):
    def __init__(
        self,
        samples: list[ZipSample],
        class_to_idx: dict[str, int],
        transform,
        max_per_class: int | None = None,
        seed: int = 42,
    ) -> None:
        grouped: dict[str, list[ZipSample]] = {}
        for sample in samples:
            grouped.setdefault(sample.class_name, []).append(sample)

        if max_per_class is not None:
            rng = random.Random(seed)
            balanced: list[ZipSample] = []
            for class_name, items in grouped.items():
                if len(items) > max_per_class:
                    items = rng.sample(items, max_per_class)
                balanced.extend(items)
            samples = balanced

        self.samples = samples
        self.class_to_idx = class_to_idx
        self.transform = transform

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int):
        sample = self.samples[idx]
        with zipfile.ZipFile(sample.zip_path) as archive:
            data = archive.read(sample.inner_path)

        image = Image.open(BytesIO(data)).convert("RGB")
        image = self.transform(image)
        label = self.class_to_idx[sample.class_name]
        return image, label


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

    print("CUDA available:", torch.cuda.is_available())
    if torch.cuda.is_available():
        print("Current GPU:", torch.cuda.get_device_name(0))

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    data_root = Path(args.data_root)
    train_source = data_root / "01.데이터" / "1.Training" / "원천데이터_230921_add"
    val_source = data_root / "01.데이터" / "2.Validation" / "원천데이터_230921_add"

    if not train_source.exists() or not val_source.exists():
        raise FileNotFoundError(
            "Could not find dataset folders. Check --data-root path. "
            f"Expected: {train_source} and {val_source}"
        )

    print("Indexing training zip files...")
    train_samples = discover_zip_samples(train_source)
    print("Indexing validation zip files...")
    val_samples = discover_zip_samples(val_source)

    all_classes = sorted({s.class_name for s in train_samples} | {s.class_name for s in val_samples})
    class_to_idx = {name: i for i, name in enumerate(all_classes)}
    num_classes = len(all_classes)

    weights = models.ResNet18_Weights.DEFAULT
    model = models.resnet18(weights=weights)
    preprocess = weights.transforms()

    num_features = model.fc.in_features
    model.fc = nn.Linear(num_features, num_classes)
    model = model.to(device)

    train_dataset = FruitZipDataset(
        samples=train_samples,
        class_to_idx=class_to_idx,
        transform=preprocess,
        max_per_class=args.max_per_class,
        seed=args.seed,
    )
    val_dataset = FruitZipDataset(
        samples=val_samples,
        class_to_idx=class_to_idx,
        transform=preprocess,
        max_per_class=args.max_per_class,
        seed=args.seed,
    )

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

    print(f"Train samples: {len(train_dataset)}")
    print(f"Validation samples: {len(val_dataset)}")
    print(f"Class count: {num_classes}")
    print("Training start")

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
            model,
            val_loader,
            criterion,
            device,
        )

        print(
            f"Epoch {epoch + 1}/{args.epochs} | "
            f"Train Loss: {train_loss:.4f}, Train Acc: {train_acc * 100:.2f}% | "
            f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc * 100:.2f}%"
        )
        print(
            f"Val Precision: {val_precision * 100:.2f}% | "
            f"Val Recall: {val_recall * 100:.2f}% | "
            f"Val F1: {val_f1 * 100:.2f}%"
        )

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            checkpoint = {
                "weights": model.state_dict(),
                "classes": all_classes,
                "class_to_idx": class_to_idx,
                "num_classes": num_classes,
                "model_name": "resnet18",
                "best_val_acc": best_val_acc,
                "image_transform": "ResNet18_Weights.DEFAULT.transforms()",
            }
            torch.save(checkpoint, save_path)
            print(f"Best model saved to: {save_path} (Val Acc: {best_val_acc * 100:.2f}%)")

    print("Training done")


@torch.no_grad()
def predict_image(image_path: str, checkpoint_path: str = "fruit_grade_resnet18.pth"):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    ckpt = torch.load(checkpoint_path, map_location=device)

    classes = ckpt["classes"]
    num_classes = ckpt["num_classes"]

    weights = models.ResNet18_Weights.DEFAULT
    model = models.resnet18(weights=None)
    model.fc = nn.Linear(model.fc.in_features, num_classes)
    model.load_state_dict(ckpt["weights"])
    model = model.to(device)
    model.eval()

    transform = weights.transforms()
    image = Image.open(image_path).convert("RGB")
    tensor = transform(image).unsqueeze(0).to(device)

    logits = model(tensor)
    probs = torch.softmax(logits, dim=1)
    conf, pred = torch.max(probs, dim=1)
    pred_class = classes[pred.item()]
    fruit_name, grade, grade_label_kr = split_class_name(pred_class)

    return {
        "predicted_class": pred_class,
        "fruit_name": fruit_name,
        "grade": grade,
        "grade_label_kr": grade_label_kr,
        "confidence": float(conf.item()),
    }


def parse_args():
    parser = argparse.ArgumentParser(description="Train fruit-grade classifier with QC zip dataset")
    parser.add_argument(
        "--data-root",
        type=str,
        default="068.농산물 품질(QC) 이미지",
        help="Path to dataset root containing 01.데이터",
    )
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument(
        "--max-per-class",
        type=int,
        default=None,
        help="Optional cap for number of images per class (useful when training quickly)",
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--save-path", type=str, default="fruit_grade_resnet18.pth")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    train(args)