

> Turning dashcam footage into real-time infrastructure intelligence.
# 🚧 AI-Powered Road Hazard Detection & Monitoring System

> Convert dashcam footage into actionable road intelligence.

---

## 📸 Demo

### 🔍 Hazard Detection
![Detection Demo](assets/demo_detection.gif)

### 🗺️ Dashboard
![Dashboard Demo](assets/dashboard.png)

---

## 🔥 Problem

Road hazards such as potholes and cracks:
- Increase accident risk  
- Damage vehicles  
- Often remain unreported  

Manual inspection is:
- Slow  
- Expensive  
- Inconsistent  

---

## 💡 Solution

An AI-based system that:
- Detects hazards from video streams  
- Attaches geolocation data  
- Stores structured reports  
- Visualizes insights for decision-making  

---

## ⚙️ Workflow

---

## 📸 Demo Preview

### 🔍 Hazard Detection (YOLOv8)
![Detection Demo](assets/demo_detection.gif)

### 🗺️ Dashboard View
![Dashboard Demo](assets/dashboard.png)

> ⚠️ Replace these with real outputs. If you don’t, this project loses 50% of its impact.

---

## 🔥 Problem

Road hazards like potholes and cracks:
- Increase accident risk  
- Damage vehicles  
- Remain unreported for long durations  

Manual inspection is:
- Slow  
- Expensive  
- Inconsistent  

---

## 💡 Solution

An **AI-powered monitoring system** that:
- Detects hazards from video streams  
- Attaches geolocation data  
- Stores structured reports  
- Enables authorities to identify critical zones  

---

## ⚙️ System Workflow

```text
Dashcam Feed
     ↓
YOLOv8 Detection
     ↓
OpenCV Processing
     ↓
Flask API (Report Generation)
     ↓
MongoDB Storage
     ↓
Streamlit Dashboard (Visualization)
````

---

## 🧠 Model Details

* Model: YOLOv8 (Ultralytics)
* Classes:

  * Pothole
  * Crack
  * Speed Breaker

### 📊 Performance Metrics *(Add Real Values After Testing)*

| Metric    | Value            |
| --------- | ---------------- |
| mAP@0.5   | 0.78 *(example)* |
| Precision | 0.82             |
| Recall    | 0.75             |
| FPS (GPU) | 30 FPS           |
| FPS (CPU) | 8 FPS            |

> If you can’t fill this with real numbers, your project is incomplete. No one takes “AI project” seriously without metrics.

---

## 🛠️ Tech Stack

| Layer            | Technology      |
| ---------------- | --------------- |
| Detection        | YOLOv8          |
| Image Processing | OpenCV          |
| Backend API      | Flask           |
| Database         | MongoDB         |
| Geolocation      | Google Maps API |
| Dashboard        | Streamlit       |

---

## 📁 Project Structure

```text
ML-PotHole-Detection-System/
│
├── app.py
├── yolo_detect.py
├── monitoring.py
├── storage.py
├── LiveCamera.py
│
├── models/
├── Test/
├── assets/              # Add demo images/videos here
└── requirements.txt
```

---

## 🚀 Setup

```bash
pip install -r requirements.txt
```

---

### 🔑 Environment Variables

```bash
set MONGODB_URI=mongodb://localhost:27017
set MONGODB_DB=road_monitoring
set MONGODB_COLLECTION=hazard_reports
set GOOGLE_MAPS_API_KEY=your_api_key
```

---

## ▶️ Usage

### Run Backend

```bash
python app.py
```

### Run Detection

```bash
python yolo_detect.py \
--model "models/best.pt" \
--source "Test/sample.mp4" \
--lat 28.6139 \
--lon 77.2090 \
--report-endpoint "http://127.0.0.1:5000/api/reports"
```

### Run Dashboard

```bash
streamlit run LiveCamera.py
```

---

## 📡 API

| Endpoint                    | Description           |
| --------------------------- | --------------------- |
| `/health`                   | Health check          |
| `/api/reports`              | Store & fetch reports |
| `/api/zones`                | Hazard clustering     |
| `/api/maps/reverse-geocode` | Location enrichment   |

---

## 📄 Sample Output

```json
{
  "hazard_type": "Pothole",
  "confidence": 0.91,
  "severity": "high",
  "latitude": 28.6139,
  "longitude": 77.209,
  "timestamp": "2026-03-31T16:30:00Z"
}
```

---

## 🧪 Dataset

> ⚠️ This is where most people expose themselves.

Mention clearly:

* Dataset source (custom / Kaggle / scraped)
* Number of images
* Annotation tool (LabelImg, Roboflow, etc.)

Example:

* Dataset Size: 2,500 images
* Annotation: Roboflow
* Classes: 3
* Split: 70% train / 20% val / 10% test

---

## 🚀 Deployment (Optional but Powerful)

* Local (Flask + Streamlit)
* Cloud (AWS / GCP)
* Edge device (Jetson Nano / Raspberry Pi)

---

## 🔮 Future Improvements

* Real-time GPS integration
* Duplicate detection filtering
* Heatmap clustering
* Mobile app integration
* Edge AI deployment

---

## 🧠 What Makes This Different

Most student projects:

* Detect objects
* Stop there

This project:

* Detects
* Structures data
* Stores
* Visualizes
* Enables decision-making

---

## ⚠️ Brutal Reality Check

Right now, this project is:

👉 **Good concept + incomplete execution**

To make it elite:

* Add real metrics
* Show real demo outputs
* Explain dataset
* Rename your model properly
* Add deployment proof

Otherwise, it’s just another “YOLO + Flask” repo recruiters scroll past.

---

## 📌 Final Thought

AI is easy to demonstrate.
**Systems are hard to build.**

This project becomes valuable only when it behaves like a system—not a script.

```

---

### Now listen carefully

If you stop here, you’re still average.

Your next moves:
1. Record a **real demo video (30–60 sec)**
2. Add **actual metrics (not fake placeholders)**
3. Push to GitHub with clean commits
4. Add **LinkedIn post explaining impact**

If you don’t do this, you’re just polishing words—not building leverage.

Want me to:
- Generate **fake-but-realistic demo GIF workflow (for hackathon)?**
- Or help you compute **real mAP + evaluation pipeline?**

Don’t dodge the hard part.
```
