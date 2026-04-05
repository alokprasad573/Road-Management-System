from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta
from typing import Any, Dict, List

import certifi

from bson import ObjectId
from pymongo import MongoClient
from pymongo.collection import Collection

from config import Config


_client: MongoClient | None = None
_collection: Collection | None = None
_memory_store: List[Dict[str, Any]] = []
_initialized = False


def initialize_storage() -> Collection | None:
    """Initialize the singleton MongoDB connection if possible."""
    global _client, _collection, _initialized

    if _initialized:
        return _collection

    _initialized = True
    try:
        _client = MongoClient(Config.MONGO_URI, serverSelectionTimeoutMS=5000, tlsCAFile=certifi.where())
        _client.admin.command("ping")
        _collection = _client[Config.MONGO_DB][Config.MONGO_COLLECTION]
        _collection.create_index("timestamp")
        _collection.create_index("status")
        _collection.create_index("zone")
        Config.DB_CONNECTED = True
        print("[DB] MongoDB connection ready.")
        return _collection
    except Exception as exc:
        import traceback
        traceback.print_exc()
        Config.DB_CONNECTED = False
        print(f"[DB][WARN] MongoDB unavailable, using in-memory fallback. {exc}")
        _collection = None
        return None


def _normalize_document(document: Dict[str, Any]) -> Dict[str, Any]:
    """Convert Mongo-specific values into JSON-friendly types."""
    payload = dict(document)
    if "_id" in payload:
        payload["_id"] = str(payload["_id"])
    return payload


def save_pothole(report: dict) -> str:
    """Save one pothole report. Return inserted ID as string."""
    initialize_storage()
    try:
        payload = dict(report)
        if _collection is not None:
            result = _collection.insert_one(payload)
            return str(result.inserted_id)

        report_id = str(ObjectId())
        payload["_id"] = report_id
        _memory_store.append(payload)
        return report_id
    except Exception as exc:
        print(f"[DB][ERROR] Failed to save pothole report: {exc}")
        raise


def get_all_potholes(limit: int = 50) -> list:
    """Return latest N potholes sorted by timestamp descending."""
    initialize_storage()
    try:
        if _collection is not None:
            rows = _collection.find().sort("timestamp", -1).limit(limit)
            return [_normalize_document(row) for row in rows]
        return sorted(_memory_store, key=lambda item: item.get("timestamp", ""), reverse=True)[:limit]
    except Exception as exc:
        print(f"[DB][ERROR] Failed to fetch potholes: {exc}")
        return []


def get_counts() -> dict:
    """Return {total, pending, fixed, in_progress, high_severity}."""
    try:
        records = get_all_potholes(limit=10000)
        return {
            "total": len(records),
            "pending": sum(1 for item in records if item.get("status") == "Pending"),
            "fixed": sum(1 for item in records if item.get("status") == "Fixed"),
            "in_progress": sum(1 for item in records if item.get("status") == "In Progress"),
            "high_severity": sum(1 for item in records if item.get("severity") == "High"),
        }
    except Exception as exc:
        print(f"[DB][ERROR] Failed to calculate counts: {exc}")
        return {"total": 0, "pending": 0, "fixed": 0, "in_progress": 0, "high_severity": 0}


def get_hourly_counts(hours: int = 8) -> list:
    """Return [{hour: '10:00', count: 5}, ...] for last N hours."""
    try:
        now = datetime.now()
        records = get_all_potholes(limit=10000)
        output = []
        for offset in reversed(range(hours)):
            slot = now - timedelta(hours=offset)
            label = slot.strftime("%H:00")
            count = 0
            for record in records:
                try:
                    ts = datetime.fromisoformat(str(record.get("timestamp")))
                except Exception:
                    continue
                if ts.strftime("%Y-%m-%d %H") == slot.strftime("%Y-%m-%d %H"):
                    count += 1
            output.append({"hour": label, "count": count})
        return output
    except Exception as exc:
        print(f"[DB][ERROR] Failed to calculate hourly counts: {exc}")
        return []


def get_zone_counts() -> list:
    """Return [{zone: 'MG Road', count: 12}, ...] sorted by count."""
    try:
        counts = Counter(str(record.get("zone", "Unknown Zone")) for record in get_all_potholes(limit=10000))
        return [{"zone": zone, "count": count} for zone, count in counts.most_common()]
    except Exception as exc:
        print(f"[DB][ERROR] Failed to calculate zone counts: {exc}")
        return []


def get_status_counts() -> dict:
    """Return {Pending: N, Fixed: N, In Progress: N}."""
    try:
        counts = Counter(str(record.get("status", "Pending")) for record in get_all_potholes(limit=10000))
        return {
            "Pending": counts.get("Pending", 0),
            "Fixed": counts.get("Fixed", 0),
            "In Progress": counts.get("In Progress", 0),
        }
    except Exception as exc:
        print(f"[DB][ERROR] Failed to calculate status counts: {exc}")
        return {"Pending": 0, "Fixed": 0, "In Progress": 0}


def get_severity_counts() -> dict:
    """Return {High: N, Medium: N, Low: N}."""
    try:
        counts = Counter(str(record.get("severity", "Medium")) for record in get_all_potholes(limit=10000))
        return {"High": counts.get("High", 0), "Medium": counts.get("Medium", 0), "Low": counts.get("Low", 0)}
    except Exception as exc:
        print(f"[DB][ERROR] Failed to calculate severity counts: {exc}")
        return {"High": 0, "Medium": 0, "Low": 0}


def mark_as_fixed(pothole_id: str) -> bool:
    """Update status to Fixed. Return True if successful."""
    initialize_storage()
    try:
        if _collection is not None:
            result = _collection.update_one(
                {"_id": ObjectId(pothole_id)},
                {"$set": {"status": "Fixed", "updated_at": datetime.now().isoformat()}},
            )
            return result.modified_count > 0

        for record in _memory_store:
            if str(record.get("_id")) == pothole_id:
                record["status"] = "Fixed"
                record["updated_at"] = datetime.now().isoformat()
                return True
        return False
    except Exception as exc:
        print(f"[DB][ERROR] Failed to mark pothole as fixed: {exc}")
        return False


def seed_dummy_data(count: int = 25):
    """If collection is empty, insert dummy pothole records for testing."""
    try:
        if get_all_potholes(limit=1):
            return

        base_time = datetime.now()
        zones = ["MG Road", "Indiranagar", "Jayanagar", "Whitefield", "Koramangala"]
        severities = ["High", "Medium", "Low"]
        statuses = ["Pending", "In Progress", "Fixed"]
        for index in range(count):
            lat = 12.9716 + (index * 0.0001)
            lng = 77.5946 + (index * 0.0001)
            save_pothole(
                {
                    "hazard_type": "Pothole",
                    "lat": lat,
                    "lng": lng,
                    "address": f"{zones[index % len(zones)]} Main Road, Bengaluru",
                    "zone": zones[index % len(zones)],
                    "maps_link": f"https://www.google.com/maps/search/?api=1&query={lat},{lng}",
                    "image_path": "static/images/dummy.jpg",
                    "severity": severities[index % len(severities)],
                    "confidence": round(0.55 + ((index % 4) * 0.1), 2),
                    "status": statuses[index % len(statuses)],
                    "timestamp": (base_time - timedelta(minutes=index * 15)).isoformat(),
                }
            )
        print(f"[DB] Seeded {count} dummy pothole records.")
    except Exception as exc:
        print(f"[DB][ERROR] Failed to seed dummy data: {exc}")