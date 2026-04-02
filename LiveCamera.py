from __future__ import annotations

import os

import av
import streamlit as st
from streamlit_webrtc import WebRtcMode, webrtc_streamer

from monitoring import GPSProvider, RoadHazardMonitor


MODEL_PATH = "models/LessAccurate Model.pt"


@st.cache_resource
def get_monitor(confidence_threshold: float) -> RoadHazardMonitor | None:
    if not os.path.exists(MODEL_PATH):
        return None
    return RoadHazardMonitor(MODEL_PATH, confidence_threshold=confidence_threshold)


def main() -> None:
    st.title("Road Infrastructure Monitoring Dashboard")
    st.caption("Live detection for potholes, cracks, speed breakers, and other road hazards.")

    confidence = st.sidebar.slider("Confidence Threshold", 0.0, 1.0, 0.4, 0.05)
    latitude = st.sidebar.number_input("Latitude", value=28.6139, format="%.6f")
    longitude = st.sidebar.number_input("Longitude", value=77.2090, format="%.6f")
    gps_provider = GPSProvider(latitude, longitude)
    monitor = get_monitor(confidence)

    if monitor is None:
        st.error(f"Model not found at {MODEL_PATH}")
        return

    def video_frame_callback(frame):
        image = frame.to_ndarray(format="bgr24")
        detections = monitor.detect(image, gps_provider=gps_provider, include_image=False)
        annotated = monitor.annotate(image.copy(), detections)
        return av.VideoFrame.from_ndarray(annotated, format="bgr24")

    webrtc_streamer(
        key="road-monitoring",
        mode=WebRtcMode.SENDRECV,
        video_frame_callback=video_frame_callback,
        async_processing=True,
        media_stream_constraints={
            "video": {
                "width": {"ideal": 1280},
                "height": {"ideal": 720},
                "frameRate": {"ideal": 30},
            },
            "audio": False,
        },
        rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
    )


if __name__ == "__main__":
    main()
