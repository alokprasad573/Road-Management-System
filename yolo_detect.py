from __future__ import annotations

import argparse
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List

import cv2

os.environ.setdefault("YOLO_CONFIG_DIR", str(Path(__file__).resolve().parent / "Ultralytics"))

from ultralytics import YOLO

from config import Config


_model: YOLO | None = None
_model_name = "unloaded"


def load_model() -> YOLO:
    """Load the primary model, falling back to the secondary model if needed."""
    global _model, _model_name

    if _model is not None:
        return _model

    for label, path in (
        ("HighAccurate Model.pt", Config.HIGH_MODEL_PATH),
        ("LessAccurate Model.pt", Config.LOW_MODEL_PATH),
    ):
        try:
            _model = YOLO(path, task="detect")
            _model_name = label
            print(f"[YOLO] Loaded model: {label}")
            return _model
        except Exception as exc:
            print(f"[YOLO][WARN] Failed to load {label}: {exc}")
    raise RuntimeError("No YOLO model could be loaded.")


def get_model_status() -> str:
    """Return the current model status string."""
    try:
        load_model()
    except Exception:
        return "unloaded"
    return _model_name


def _severity_from_confidence(confidence: float) -> str:
    """Map detection confidence to a severity label."""
    if confidence >= 0.85:
        return "High"
    if confidence >= 0.65:
        return "Medium"
    return "Low"


def _save_annotated_frame(frame, boxes: Iterable[Dict[str, object]]) -> str:
    """Draw boxes on a frame and save it to disk."""
    output = frame.copy()
    for item in boxes:
        x1, y1, x2, y2 = item["bbox"]
        confidence = float(item["confidence"])
        label = str(item["label"])
        color = (56, 189, 248)
        cv2.rectangle(output, (x1, y1), (x2, y2), color, 2)
        cv2.putText(
            output,
            f"{label} {confidence:.2f}",
            (x1, max(25, y1 - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            color,
            2,
        )

    Path(Config.STATIC_IMAGE_DIR).mkdir(parents=True, exist_ok=True)
    filename = f"frame_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.jpg"
    output_path = str(Path(Config.STATIC_IMAGE_DIR) / filename)
    cv2.imwrite(output_path, output)
    return output_path


def detect_frame(frame) -> Dict[str, object]:
    """Run YOLO detection on a frame and return the best matching result."""
    model = load_model()
    results = model(frame, verbose=False)
    boxes = results[0].boxes
    candidates: List[Dict[str, object]] = []
    names = model.names

    for index in range(len(boxes)):
        confidence = float(boxes[index].conf.item())
        if confidence < Config.CONFIDENCE_THRESHOLD:
            continue
        coords = boxes[index].xyxy.cpu().numpy().squeeze().astype(int).tolist()
        class_index = int(boxes[index].cls.item())
        label = str(names[class_index])
        candidates.append(
            {
                "confidence": confidence,
                "bbox": coords,
                "label": label,
                "severity": _severity_from_confidence(confidence),
            }
        )

    if not candidates:
        return {"detected": False, "confidence": 0.0, "bbox": [], "image_path": "", "severity": "Low"}

    best = max(candidates, key=lambda item: item["confidence"])
    image_path = _save_annotated_frame(frame, candidates)
    return {
        "detected": True,
        "confidence": best["confidence"],
        "bbox": best["bbox"],
        "image_path": image_path,
        "severity": best["severity"],
    }


def detect_image_file(image_path: str) -> Dict[str, object]:
    """Run detection on a single image file."""
    frame = cv2.imread(image_path)
    if frame is None:
        raise FileNotFoundError(f"Unable to read image: {image_path}")
    result = detect_frame(frame)
    print(f"[YOLO][IMAGE] {image_path} -> {result}")
    return result


def detect_video_file(video_path: str, max_frames: int | None = 25) -> List[Dict[str, object]]:
    """Run detection on a video file and print frame-by-frame results."""
    capture = cv2.VideoCapture(video_path)
    if not capture.isOpened():
        raise FileNotFoundError(f"Unable to open video: {video_path}")

    frame_results: List[Dict[str, object]] = []
    frame_index = 0
    while True:
        ok, frame = capture.read()
        if not ok or frame is None:
            break
        frame_index += 1
        result = detect_frame(frame)
        print(f"[YOLO][VIDEO] frame={frame_index} result={result}")
        frame_results.append(result)
        if max_frames is not None and frame_index >= max_frames:
            break
    capture.release()
    return frame_results


def parse_args() -> argparse.Namespace:
    """Parse detector CLI arguments."""
    parser = argparse.ArgumentParser(description="RoadWatch AI YOLO detector")
    parser.add_argument("--source", help="Image or video path to test.")
    return parser.parse_args()


def main() -> None:
    """Run detector tests against known assets or a custom source."""
    args = parse_args()
    load_model()

    if args.source:
        path = Path(args.source)
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".bmp"}:
            detect_image_file(str(path))
        else:
            detect_video_file(str(path))
        return

    if Path(Config.TEST_IMAGE_PATH).exists():
        detect_image_file(Config.TEST_IMAGE_PATH)
    else:
        print(f"[YOLO][WARN] Test image missing: {Config.TEST_IMAGE_PATH}")

    if Path(Config.TEST_VIDEO_PATH).exists():
        detect_video_file(Config.TEST_VIDEO_PATH)
    else:
        print(f"[YOLO][WARN] Test video missing: {Config.TEST_VIDEO_PATH}")
