from pathlib import Path
import csv
import hashlib
import shutil
from collections import defaultdict

from PIL import Image

# ============================================================
# FSOC YOLO DATASET CLEANER
# Existing input:
#   beacon_yolo_dataset/
#       images/train/
#       labels/train/
#       annotations.csv   (optional)
#
# Output:
#   beacon_yolo_dataset/cleaned/
#       images/train/
#       images/val/
#       labels/train/
#       labels/val/
#   beacon_yolo_dataset/cleaning_report.csv
#   beacon_yolo_dataset/data.yaml
#
# IMPORTANT:
# The original images/ and labels/ are NOT deleted.
# ============================================================

ROOT = Path(__file__).resolve().parent
SRC_IMAGES = ROOT / "images" / "train"
SRC_LABELS = ROOT / "labels" / "train"

OUT = ROOT / "cleaned"
OUT_TRAIN_IMAGES = OUT / "images" / "train"
OUT_VAL_IMAGES = OUT / "images" / "val"
OUT_TRAIN_LABELS = OUT / "labels" / "train"
OUT_VAL_LABELS = OUT / "labels" / "val"

for folder in [
    OUT_TRAIN_IMAGES, OUT_VAL_IMAGES,
    OUT_TRAIN_LABELS, OUT_VAL_LABELS
]:
    folder.mkdir(parents=True, exist_ok=True)

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

# Near-duplicate threshold.
# Lower = stricter. 6 is a reasonable starting point for synthetic frames.
PHASH_THRESHOLD = 6

# Keep consecutive frames from the same run together when splitting.
# This helps prevent almost-identical frames leaking into both train/val.
BLOCK_SIZE = 30


def file_hash(path):
    """Exact duplicate detector."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def average_hash(path, size=16):
    """Small dependency-free perceptual hash."""
    with Image.open(path) as im:
        im = im.convert("L").resize((size, size), Image.Resampling.LANCZOS)

        pixels = list(im.getdata())
        avg = sum(pixels) / len(pixels)

        bits = 0
        for p in pixels:
            bits = (bits << 1) | int(p >= avg)

        return bits


def hamming_distance(a, b):
    return (a ^ b).bit_count()


def validate_label(label_path):
    """
    Validate YOLO detection label:
        class_id x_center y_center width height
    Returns:
        (True, reason) or (False, reason)
    """
    try:
        lines = label_path.read_text(encoding="utf-8").splitlines()
    except Exception as e:
        return False, f"label_read_error:{e}"

    if not lines:
        return False, "empty_label"

    valid_rows = []

    for line_no, line in enumerate(lines, 1):
        parts = line.strip().split()

        if len(parts) != 5:
            return False, f"invalid_columns_line_{line_no}"

        try:
            class_id = int(float(parts[0]))
            xc, yc, w, h = map(float, parts[1:])
        except ValueError:
            return False, f"non_numeric_line_{line_no}"

        if class_id < 0:
            return False, f"negative_class_line_{line_no}"

        # YOLO normalized coordinates must be in [0, 1].
        if not all(0.0 <= v <= 1.0 for v in (xc, yc, w, h)):
            return False, f"coordinate_out_of_range_line_{line_no}"

        if w <= 0 or h <= 0:
            return False, f"zero_or_negative_box_line_{line_no}"

        # A normalized box must fit within the image.
        if xc - w / 2 < 0 or xc + w / 2 > 1:
            return False, f"box_outside_x_line_{line_no}"

        if yc - h / 2 < 0 or yc + h / 2 > 1:
            return False, f"box_outside_y_line_{line_no}"

        valid_rows.append(line)

    return True, "valid"


def read_csv_metadata():
    csv_path = ROOT / "annotations.csv"
    metadata = {}

    if not csv_path.exists():
        return metadata

    try:
        with open(csv_path, "r", encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                image_name = row.get("image", "").strip()
                if image_name:
                    metadata[image_name] = row
    except Exception as e:
        print(f"WARNING: Could not read annotations.csv: {e}")

    return metadata


def main():
    if not SRC_IMAGES.exists():
        raise FileNotFoundError(f"Images folder not found: {SRC_IMAGES}")

    if not SRC_LABELS.exists():
        raise FileNotFoundError(f"Labels folder not found: {SRC_LABELS}")

    metadata = read_csv_metadata()

    image_files = sorted(
        p for p in SRC_IMAGES.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS
    )

    print("=" * 60)
    print("FSOC YOLO DATASET CLEANING")
    print("=" * 60)
    print(f"Input images: {len(image_files)}")
    print(f"Input folder: {SRC_IMAGES}")
    print()

    report = []

    exact_seen = {}
    phash_seen = []

    valid_items = []

    counts = defaultdict(int)

    # ------------------------------------------------------------
    # PASS 1: validate image + matching label + YOLO annotation
    # ------------------------------------------------------------
    for image_path in image_files:
        name = image_path.name
        label_path = SRC_LABELS / f"{image_path.stem}.txt"

        try:
            with Image.open(image_path) as im:
                im.verify()

            # Open once more after verify.
            with Image.open(image_path) as im:
                width, height = im.size

            if width < 32 or height < 32:
                counts["tiny_image"] += 1
                report.append([name, "REMOVED", "image_too_small"])
                continue

        except Exception as e:
            counts["corrupt_image"] += 1
            report.append([name, "REMOVED", f"corrupt_image:{e}"])
            continue

        if not label_path.exists():
            counts["missing_label"] += 1
            report.append([name, "REMOVED", "missing_label"])
            continue

        ok, reason = validate_label(label_path)
        if not ok:
            counts["invalid_label"] += 1
            report.append([name, "REMOVED", reason])
            continue

        # --------------------------------------------------------
        # Exact duplicate check
        # --------------------------------------------------------
        try:
            sha = file_hash(image_path)
        except Exception as e:
            counts["hash_error"] += 1
            report.append([name, "REMOVED", f"hash_error:{e}"])
            continue

        if sha in exact_seen:
            counts["exact_duplicate"] += 1
            report.append([
                name, "REMOVED",
                f"exact_duplicate_of:{exact_seen[sha]}"
            ])
            continue

        exact_seen[sha] = name

        # --------------------------------------------------------
        # Near duplicate check
        # --------------------------------------------------------
        try:
            phash = average_hash(image_path)
        except Exception as e:
            counts["phash_error"] += 1
            report.append([name, "REMOVED", f"phash_error:{e}"])
            continue

        near_duplicate = None

        for old_hash, old_name in phash_seen:
            distance = hamming_distance(phash, old_hash)
            if distance <= PHASH_THRESHOLD:
                near_duplicate = old_name
                break

        if near_duplicate is not None:
            counts["near_duplicate"] += 1
            report.append([
                name, "REMOVED",
                f"near_duplicate_of:{near_duplicate}"
            ])
            continue

        phash_seen.append((phash, name))

        valid_items.append({
            "image": image_path,
            "label": label_path,
            "name": name,
            "phash": phash,
            "metadata": metadata.get(name, {})
        })

    # ------------------------------------------------------------
    # PASS 2: split by contiguous blocks
    # ------------------------------------------------------------
    # Do NOT randomly split synthetic video frames.
    # Consecutive frames are often almost identical.
    train_items = []
    val_items = []

    for block_index in range(0, len(valid_items), BLOCK_SIZE):
        block = valid_items[block_index:block_index + BLOCK_SIZE]

        # Approximately 80/20 while keeping blocks intact.
        group_number = block_index // BLOCK_SIZE
        if group_number % 5 == 4:
            val_items.extend(block)
        else:
            train_items.extend(block)

    # ------------------------------------------------------------
    # PASS 3: copy cleaned dataset
    # ------------------------------------------------------------
    for item in train_items:
        shutil.copy2(
            item["image"],
            OUT_TRAIN_IMAGES / item["name"]
        )
        shutil.copy2(
            item["label"],
            OUT_TRAIN_LABELS / f'{item["image"].stem}.txt'
        )

        report.append([item["name"], "KEPT", "train"])

    for item in val_items:
        shutil.copy2(
            item["image"],
            OUT_VAL_IMAGES / item["name"]
        )
        shutil.copy2(
            item["label"],
            OUT_VAL_LABELS / f'{item["image"].stem}.txt'
        )

        report.append([item["name"], "KEPT", "val"])

    # ------------------------------------------------------------
    # Cleaning report
    # ------------------------------------------------------------
    report_path = ROOT / "cleaning_report.csv"

    with open(report_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["image", "action", "reason"])
        writer.writerows(report)

    # ------------------------------------------------------------
    # YOLO data.yaml
    # ------------------------------------------------------------
    yaml_path = ROOT / "data.yaml"

    # Use forward slashes for YAML/Windows compatibility.
    train_path = (OUT_TRAIN_IMAGES).resolve().as_posix()
    val_path = (OUT_VAL_IMAGES).resolve().as_posix()

    yaml_text = f"""# FSOC Beacon YOLO Dataset
path: {ROOT.resolve().as_posix()}
train: {train_path}
val: {val_path}

nc: 1
names:
  0: beacon
"""

    yaml_path.write_text(yaml_text, encoding="utf-8")

    print()
    print("=" * 60)
    print("CLEANING COMPLETE")
    print("=" * 60)
    print(f"Original images       : {len(image_files)}")
    print(f"Corrupt images        : {counts['corrupt_image']}")
    print(f"Missing labels        : {counts['missing_label']}")
    print(f"Invalid labels        : {counts['invalid_label']}")
    print(f"Exact duplicates      : {counts['exact_duplicate']}")
    print(f"Near duplicates       : {counts['near_duplicate']}")
    print(f"Too-small images      : {counts['tiny_image']}")
    print(f"Final valid images    : {len(valid_items)}")
    print(f"Training images       : {len(train_items)}")
    print(f"Validation images     : {len(val_items)}")
    print()
    print(f"Cleaned dataset: {OUT}")
    print(f"Cleaning report: {report_path}")
    print(f"YOLO data.yaml:   {yaml_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
