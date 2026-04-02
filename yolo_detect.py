from __future__ import annotations

import argparse
import json
import os
import sys
from typing import List, Optional, Tuple

import requests

from monitoring import DetectionEvent, GPSProvider, RoadHazardMonitor


os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Detect road hazards from images, video, or dashcam streams and optionally report them."
    )
    parser.add_argument("--model", required=True, help='Path to YOLO model file, e.g. "models/LessAccurate Model.pt"')
    parser.add_argument("--source", required=True, help='Image, video, or camera source like "usb0"')
    parser.add_argument("--thresh", type=float, default=0.5, help="Minimum confidence threshold")
    parser.add_argument("--resolution", default=None, help='Optional resize target in WxH format, e.g. "1280x720"')
    parser.add_argument("--lat", type=float, default=None, help="Manual latitude for detections")
    parser.add_argument("--lon", type=float, default=None, help="Manual longitude for detections")
    parser.add_argument("--report-endpoint", default=None, help="Flask API endpoint to receive detection reports")
    parser.add_argument("--report-batch-size", type=int, default=1, help="Number of detections to send per request")
    parser.add_argument("--include-image", action="store_true", help="Attach the encoded evidence frame in each report")
    parser.add_argument("--print-json", action="store_true", help="Print detections as JSON to stdout")
    return parser.parse_args()


def parse_resolution(value: Optional[str]) -> Optional[Tuple[int, int]]:
    if not value:
        return None
    try:
        width, height = map(int, value.lower().split("x"))
        return width, height
    except ValueError as exc:
        raise ValueError('Invalid resolution format. Use "WIDTHxHEIGHT".') from exc


def post_reports(endpoint: str, detections: List[DetectionEvent], batch_size: int) -> None:
    for start in range(0, len(detections), batch_size):
        batch = detections[start : start + batch_size]
        if len(batch) == 1:
            payload = batch[0].to_dict()
        else:
            payload = {"reports": [detection.to_dict() for detection in batch]}
        response = requests.post(endpoint, json=payload, timeout=10)
        response.raise_for_status()


def main() -> int:
    args = parse_args()

    if not os.path.exists(args.model):
        print(f'ERROR: Model path "{args.model}" is invalid or model was not found.')
        return 1

    try:
        resize_to = parse_resolution(args.resolution)
        monitor = RoadHazardMonitor(args.model, confidence_threshold=args.thresh)
        gps_provider = GPSProvider(args.lat, args.lon)
    except Exception as exc:
        print(f"ERROR: Failed to initialize monitoring pipeline. {exc}")
        return 1

    def handle_detections(detections: List[DetectionEvent]) -> None:
        if args.print_json:
            print(json.dumps([detection.to_dict() for detection in detections], indent=2))
        if args.report_endpoint:
            post_reports(args.report_endpoint, detections, args.report_batch_size)

    try:
        monitor.process_stream(
            source=args.source,
            gps_provider=gps_provider,
            include_image=args.include_image,
            on_detection=handle_detections,
            resize_to=resize_to,
        )
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
