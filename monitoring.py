from __future__ import annotations

import base64
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Dict, Iterable, List, Optional, Tuple

import cv2
from ultralytics import YOLO

from google_maps import build_google_maps_url


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class DetectionEvent:
    hazard_type: str
    confidence: float
    bbox: List[int]
    timestamp: str
    frame_width: int
    frame_height: int
    severity: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    google_maps_url: Optional[str] = None
    image_base64: Optional[str] = None

    def to_dict(self) -> Dict[str, object]:
        return {
            "hazard_type": self.hazard_type,
            "confidence": round(self.confidence, 4),
            "bbox": self.bbox,
            "timestamp": self.timestamp,
            "frame_width": self.frame_width,
            "frame_height": self.frame_height,
            "severity": self.severity,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "google_maps_url": self.google_maps_url,
            "image_base64": self.image_base64,
        }


class GPSProvider:
    def __init__(self, latitude: Optional[float] = None, longitude: Optional[float] = None) -> None:
        self.latitude = latitude
        self.longitude = longitude

    def get_coordinates(self) -> Tuple[Optional[float], Optional[float]]:
        return self.latitude, self.longitude


class RoadHazardMonitor:
    def __init__(self, model_path: str, confidence_threshold: float = 0.5) -> None:
        self.model = YOLO(model_path, task="detect")
        self.labels = self.model.names
        self.confidence_threshold = confidence_threshold
        self.colors = [
            (164, 120, 87),
            (68, 148, 228),
            (93, 97, 209),
            (178, 182, 133),
            (88, 159, 106),
            (96, 202, 231),
            (159, 124, 168),
            (169, 162, 241),
            (98, 118, 150),
            (172, 176, 184),
        ]

    def detect(
        self,
        frame,
        gps_provider: Optional[GPSProvider] = None,
        include_image: bool = False,
    ) -> List[DetectionEvent]:
        results = self.model(frame, verbose=False)
        detections = results[0].boxes
        frame_height, frame_width = frame.shape[:2]
        latitude, longitude = (gps_provider.get_coordinates() if gps_provider else (None, None))
        encoded_frame = encode_frame_to_base64(frame) if include_image else None

        events: List[DetectionEvent] = []
        for idx in range(len(detections)):
            confidence = float(detections[idx].conf.item())
            if confidence < self.confidence_threshold:
                continue

            class_index = int(detections[idx].cls.item())
            label = self.labels[class_index]
            xyxy = detections[idx].xyxy.cpu().numpy().squeeze().astype(int).tolist()
            events.append(
                DetectionEvent(
                    hazard_type=label,
                    confidence=confidence,
                    bbox=xyxy,
                    timestamp=utc_timestamp(),
                    frame_width=frame_width,
                    frame_height=frame_height,
                    severity=calculate_severity(label, confidence),
                    latitude=latitude,
                    longitude=longitude,
                    google_maps_url=build_google_maps_url(latitude, longitude),
                    image_base64=encoded_frame,
                )
            )
        return events

    def annotate(self, frame, detections: Iterable[DetectionEvent]):
        for event in detections:
            xmin, ymin, xmax, ymax = event.bbox
            color = self.colors[hash(event.hazard_type) % len(self.colors)]
            cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), color, 2)
            label = f"{event.hazard_type} {int(event.confidence * 100)}% | {event.severity}"
            label_size, baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            label_y = max(ymin, label_size[1] + 10)
            cv2.rectangle(
                frame,
                (xmin, label_y - label_size[1] - 10),
                (xmin + label_size[0], label_y + baseline - 10),
                color,
                cv2.FILLED,
            )
            cv2.putText(
                frame,
                label,
                (xmin, label_y - 7),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 0, 0),
                1,
            )
        return frame

    def process_stream(
        self,
        source: str,
        gps_provider: Optional[GPSProvider] = None,
        include_image: bool = False,
        on_detection: Optional[Callable[[List[DetectionEvent]], None]] = None,
        resize_to: Optional[Tuple[int, int]] = None,
        preview_window: str = "Road Hazard Monitoring",
    ) -> None:
        cap, source_type, images = resolve_source(source)
        image_index = 0

        while True:
            frame = None
            if source_type == "image":
                if image_index >= len(images):
                    break
                frame = cv2.imread(images[image_index])
                image_index += 1
                if frame is None:
                    continue
            else:
                ret, frame = cap.read()
                if not ret or frame is None:
                    break

            if resize_to:
                frame = cv2.resize(frame, resize_to)

            detections = self.detect(frame, gps_provider=gps_provider, include_image=include_image)
            if detections and on_detection:
                on_detection(detections)

            annotated_frame = self.annotate(frame.copy(), detections)
            cv2.imshow(preview_window, annotated_frame)

            key = cv2.waitKey(0 if source_type == "image" else 5)
            if key in [ord("q"), ord("Q"), 27]:
                break

        if cap is not None:
            cap.release()
        cv2.destroyAllWindows()


def resolve_source(source: str):
    image_extensions = {".jpg", ".jpeg", ".png", ".bmp"}
    video_extensions = {".avi", ".mov", ".mp4", ".mkv", ".wmv"}

    if os.path.isfile(source):
        extension = os.path.splitext(source)[1].lower()
        if extension in image_extensions:
            return None, "image", [source]
        if extension in video_extensions:
            return cv2.VideoCapture(source), "video", []
        raise ValueError(f"Unsupported file type: {extension}")

    if source.startswith("usb"):
        try:
            return cv2.VideoCapture(int(source[3:])), "usb", []
        except ValueError as exc:
            raise ValueError(f"Invalid camera source '{source}'") from exc

    raise ValueError("Source must be an image file, video file, or camera index like usb0.")


def calculate_severity(label: str, confidence: float) -> str:
    normalized = label.lower()
    if "pothole" in normalized and confidence >= 0.75:
        return "high"
    if "crack" in normalized or "streetlight" in normalized:
        return "medium"
    if confidence >= 0.85:
        return "high"
    if confidence >= 0.55:
        return "medium"
    return "low"
def encode_frame_to_base64(frame) -> str:
    success, buffer = cv2.imencode(".jpg", frame)
    if not success:
        raise ValueError("Failed to encode evidence frame.")
    return base64.b64encode(buffer.tobytes()).decode("utf-8")
