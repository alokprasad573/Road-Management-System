from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parent
load_dotenv(ROOT_DIR / ".env")


def _get_required(name: str) -> str:
    """Return a required environment variable or raise a helpful error."""
    value = os.getenv(name)
    if value in (None, ""):
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _resolve_path(raw_path: str, *fallbacks: str) -> str:
    """Resolve a project path, trying fallbacks when the requested file is absent."""
    candidates = [raw_path, *fallbacks]
    for candidate in candidates:
        path = Path(candidate)
        if not path.is_absolute():
            path = ROOT_DIR / path
        if path.exists():
            return str(path)
    path = Path(raw_path)
    if not path.is_absolute():
        path = ROOT_DIR / path
    return str(path)


class Config:
    """Shared application configuration."""

    MONGO_URI = _get_required("MONGO_URI")
    MONGO_DB = _get_required("MONGO_DB")
    MONGO_COLLECTION = _get_required("MONGO_COLLECTION")
    GOOGLE_MAPS_API_KEY = _get_required("GOOGLE_MAPS_API_KEY")
    FLASK_SECRET_KEY = _get_required("FLASK_SECRET_KEY")
    FLASK_PORT = int(_get_required("FLASK_PORT"))
    CONFIDENCE_THRESHOLD = float(_get_required("CONFIDENCE_THRESHOLD"))
    DETECTION_INTERVAL = int(_get_required("DETECTION_INTERVAL"))
    HIGH_MODEL_PATH = _resolve_path(
        _get_required("HIGH_MODEL_PATH"),
        "model/HIGH Accurate Model.pt",
    )
    LOW_MODEL_PATH = _resolve_path(
        _get_required("LOW_MODEL_PATH"),
        "runs/detect/train/weights/best.pt",
        "yolo11s.pt",
    )
    STATIC_IMAGE_DIR = str(ROOT_DIR / "static" / "images")
    TEST_IMAGE_PATH = str(ROOT_DIR / "Test" / "1.png")
    TEST_VIDEO_PATH = str(ROOT_DIR / "Test" / "Pothole Exp1.mp4")
    DB_CONNECTED = False


try:
    print("✅ Config loaded successfully")
except UnicodeEncodeError:
    print("[OK] Config loaded successfully")
