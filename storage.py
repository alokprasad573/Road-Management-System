from __future__ import annotations

import os
from collections import Counter
from typing import Any, Dict, List, Optional

try:
    from pymongo import MongoClient
    from pymongo.collection import Collection
except ImportError:  # pragma: no cover - dependency is optional at runtime
    MongoClient = None
    Collection = object


class ReportStore:
    def insert_report(self, report: Dict[str, object]) -> Dict[str, object]:
        raise NotImplementedError

    def list_reports(self, filters: Optional[Dict[str, Any]] = None, limit: int = 100) -> List[Dict[str, object]]:
        raise NotImplementedError

    def summarize_hotspots(self) -> List[Dict[str, object]]:
        raise NotImplementedError


class InMemoryReportStore(ReportStore):
    def __init__(self) -> None:
        self._reports: List[Dict[str, object]] = []

    def insert_report(self, report: Dict[str, object]) -> Dict[str, object]:
        self._reports.append(report)
        return report

    def list_reports(self, filters: Optional[Dict[str, Any]] = None, limit: int = 100) -> List[Dict[str, object]]:
        filters = filters or {}
        reports = []
        for report in reversed(self._reports):
            if not matches_filters(report, filters):
                continue
            reports.append(report)
            if len(reports) >= limit:
                break
        return reports

    def summarize_hotspots(self) -> List[Dict[str, object]]:
        counts = Counter()
        for report in self._reports:
            key = (
                report.get("hazard_type", "unknown"),
                report.get("latitude"),
                report.get("longitude"),
            )
            counts[key] += 1

        return [
            {
                "hazard_type": hazard_type,
                "latitude": latitude,
                "longitude": longitude,
                "report_count": count,
            }
            for (hazard_type, latitude, longitude), count in counts.most_common()
        ]


class MongoReportStore(ReportStore):
    def __init__(self, collection: Collection) -> None:
        self.collection = collection
        self.collection.create_index("timestamp")
        self.collection.create_index("hazard_type")
        self.collection.create_index("severity")
        self.collection.create_index([("location", "2dsphere")])

    def insert_report(self, report: Dict[str, object]) -> Dict[str, object]:
        payload = dict(report)
        result = self.collection.insert_one(payload)
        payload["_id"] = str(result.inserted_id)
        return payload

    def list_reports(self, filters: Optional[Dict[str, Any]] = None, limit: int = 100) -> List[Dict[str, object]]:
        reports = []
        query = build_mongo_query(filters or {})
        for report in self.collection.find(query).sort("timestamp", -1).limit(limit):
            report["_id"] = str(report["_id"])
            reports.append(report)
        return reports

    def summarize_hotspots(self) -> List[Dict[str, object]]:
        pipeline = [
            {
                "$group": {
                    "_id": {
                        "hazard_type": "$hazard_type",
                        "latitude": "$latitude",
                        "longitude": "$longitude",
                    },
                    "report_count": {"$sum": 1},
                }
            },
            {"$sort": {"report_count": -1}},
        ]
        hotspots = []
        for item in self.collection.aggregate(pipeline):
            hotspots.append(
                {
                    "hazard_type": item["_id"].get("hazard_type"),
                    "latitude": item["_id"].get("latitude"),
                    "longitude": item["_id"].get("longitude"),
                    "report_count": item["report_count"],
                }
            )
        return hotspots


def build_report_store() -> ReportStore:
    mongo_uri = os.getenv("MONGODB_URI")
    database_name = os.getenv("MONGODB_DB", "road_monitoring")
    collection_name = os.getenv("MONGODB_COLLECTION", "hazard_reports")

    if mongo_uri and MongoClient is not None:
        client = MongoClient(mongo_uri)
        collection = client[database_name][collection_name]
        return MongoReportStore(collection)
    return InMemoryReportStore()


def matches_filters(report: Dict[str, object], filters: Dict[str, Any]) -> bool:
    for key, value in filters.items():
        if value in (None, ""):
            continue
        if report.get(key) != value:
            return False
    return True


def build_mongo_query(filters: Dict[str, Any]) -> Dict[str, Any]:
    query: Dict[str, Any] = {}
    if filters.get("hazard_type") not in (None, ""):
        query["hazard_type"] = filters["hazard_type"]
    if filters.get("severity") not in (None, ""):
        query["severity"] = filters["severity"]
    return query
