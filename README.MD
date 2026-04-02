# Automated Road Infrastructure Monitoring and Reporting

An AI-powered road monitoring system that uses YOLOv8, OpenCV, Flask, Google Maps, and MongoDB to detect road hazards from dashcam footage and generate real-time reports for maintenance teams.

## Problem Statement

Manual inspection of potholes, cracks, broken streetlights, and related road hazards is slow, costly, and inconsistent. Delays between hazard appearance and repair increase accident risk, damage vehicles, and make it harder for city authorities to prioritize critical zones.

## Proposed Solution

This project turns a dashcam or roadside video stream into an automated monitoring workflow:

1. YOLOv8 detects hazards such as potholes, cracks, and speed breakers.
2. The system attaches GPS coordinates and timestamps to each detection.
3. A Flask API stores reports in MongoDB for later review or dashboard use.
4. Authorities can query reports and hotspot summaries to identify high-priority repair zones.

## Technical Stack

- Computer Vision: YOLOv8 by Ultralytics
- Image Processing: OpenCV
- Backend API: Flask
- Geospatial Enrichment: Google Maps Geocoding API
- Storage: MongoDB via `pymongo` with in-memory fallback
- Live Dashboard: Streamlit + WebRTC
- Integration Target: Dashcam / Android Auto style camera feeds

## Project Structure

```text
ML-PotHole-Detection-System/
|-- app.py
|-- monitoring.py
|-- storage.py
|-- yolo_detect.py
|-- LiveCamera.py
|-- models/
|-- Test/
|-- requirements.txt
```

## Setup

```bash
pip install -r requirements.txt
```

Optional environment variables for MongoDB:

```bash
set MONGODB_URI=mongodb://localhost:27017
set MONGODB_DB=road_monitoring
set MONGODB_COLLECTION=hazard_reports
set GOOGLE_MAPS_API_KEY=your_google_maps_api_key
```

## Usage

Run the backend API:

```bash
python app.py
```

Run hazard detection on a video and post detections to the Flask backend:

```bash
python yolo_detect.py --model "models/LessAccurate Model.pt" --source "Test/Pothole Exp1.mp4" --lat 28.6139 --lon 77.2090 --report-endpoint "http://127.0.0.1:5000/api/reports" --report-batch-size 1 --print-json
```

Run the live web dashboard:

```bash
streamlit run LiveCamera.py
```

## API Endpoints

- `GET /health`: Service health check
- `POST /api/reports`: Store a hazard report
- `GET /api/reports`: List stored reports
- `GET /api/zones`: Summarize repeated hazard zones
- `GET /api/maps/reverse-geocode`: Enrich coordinates using Google Maps

## Example Report Payload

```json
{
  "hazard_type": "Pothole",
  "confidence": 0.91,
  "bbox": [225, 318, 410, 506],
  "timestamp": "2026-03-31T16:30:00+00:00",
  "frame_width": 1280,
  "frame_height": 720,
  "severity": "high",
  "latitude": 28.6139,
  "longitude": 77.209,
  "google_maps_url": "https://www.google.com/maps/search/?api=1&query=28.6139,77.209",
  "location": {
    "type": "Point",
    "coordinates": [77.209, 28.6139]
  },
  "geocode": {
    "formatted_address": "New Delhi, Delhi, India",
    "place_id": "sample_place_id"
  }
}
```

## Future Extensions

- Replace manual latitude and longitude with Android Auto or telematics GPS input
- Add broken streetlight and lane damage classes to the trained dataset
- Build an authority dashboard with filters, maps, and repair status tracking
- Add rate limiting and duplicate suppression for repeated detections on the same road segment
