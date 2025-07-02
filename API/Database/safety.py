from fastapi import FastAPI, APIRouter, HTTPException
from datetime import datetime, time
from pydantic import BaseModel
from typing import List
from API import api_db_handler

intrusion_collection = api_db_handler.db["intrusion"]
fall_collection = api_db_handler.db["fall"]
tampering_collection = api_db_handler.db["camera_tempering"]

router = APIRouter()

class IntrusionAlert(BaseModel):
    alert: str = "Intrusion Alert"
    reason: str = "Suspicious activity reported"
    camera_name: str
    time_elapsed: str

class FallAlert(BaseModel):
    alert: str = "Fall Detected"
    reason: str = "Person fall/slip Detected"
    camera_name: str
    time_elapsed: str

class TamperingAlert(BaseModel):
    alert: str = "Camera Tampering Detected"
    reason: str
    camera_name: str
    time_elapsed: str

class SafetyMonitoringAPI:
    def __init__(self):
        self.router = APIRouter()
        self.router.get(
            "/latest-intrusions",
            tags=["Safety Monitoring"],
            response_model=List[IntrusionAlert]
        )(self.get_latest_intrusions)
        self.router.get(
            "/latest-falls",
            tags=["Safety Monitoring"],
            response_model=List[FallAlert]
        )(self.get_latest_falls)
        self.router.get(
            "/latest-tampering",
            tags=["Safety Monitoring"],
            response_model=List[TamperingAlert]
        )(self.get_latest_tampering)

    def format_time_elapsed(self, seconds):
        seconds = abs(seconds)  # Ensure positive value
        if seconds < 60:
            return f"{int(seconds)} seconds"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{int(minutes)} minutes"
        else:
            hours = seconds // 3600
            return f"{int(hours)} hours"

    def get_latest_intrusions(self):
        date_obj = datetime.today().date()
        start = datetime.combine(date_obj, time.min)
        end = datetime.combine(date_obj, time.max)
        current_time = datetime.now()

        pipeline = [
            {"$match": {
                "timestamp": {"$gte": start, "$lte": end},
                "intrusion": True
            }},
            {"$sort": {"timestamp": -1}},
            {"$group": {
                "_id": "$camera_name",
                "latest_timestamp": {"$first": "$timestamp"},
            }},
            {"$project": {
                "alert": "Intrusion Alert",
                "reason": "Suspicious activity reported",
                "camera_name": "$_id",
                "time_elapsed": {
                    "$abs": {
                        "$divide": [
                            {"$subtract": [current_time, "$latest_timestamp"]},
                            1000
                        ]
                    }
                },
                "_id": 0
            }},
            {"$sort": {"camera_name": 1}}
        ]

        results = list(intrusion_collection.aggregate(pipeline))
        if not results:
            raise HTTPException(status_code=404, detail="No intrusion data found")
        for result in results:
            result["time_elapsed"] = self.format_time_elapsed(result["time_elapsed"])
        return [IntrusionAlert(**r) for r in results]

    def get_latest_falls(self):
        date_obj = datetime.today().date()
        start = datetime.combine(date_obj, time.min)
        end = datetime.combine(date_obj, time.max)
        current_time = datetime.now()

        pipeline = [
            {"$match": {
                "timestamp": {"$gte": start, "$lte": end},
                "Alert": True
            }},
            {"$sort": {"timestamp": -1}},
            {"$group": {
                "_id": "$camera_name",
                "latest_timestamp": {"$first": "$timestamp"},
            }},
            {"$project": {
                "alert": "Fall Detected",
                "reason": "Person fall/slip Detected",
                "camera_name": "$_id",
                "time_elapsed": {
                    "$abs": {
                        "$divide": [
                            {"$subtract": [current_time, "$latest_timestamp"]},
                            1000
                        ]
                    }
                },
                "_id": 0
            }},
            {"$sort": {"camera_name": 1}}
        ]

        results = list(fall_collection.aggregate(pipeline))
        if not results:
            raise HTTPException(status_code=404, detail="No fall detection data found")
        for result in results:
            result["time_elapsed"] = self.format_time_elapsed(result["time_elapsed"])
        return [FallAlert(**r) for r in results]

    def get_latest_tampering(self):
        date_obj = datetime.today().date()
        start = datetime.combine(date_obj, time.min)
        end = datetime.combine(date_obj, time.max)
        current_time = datetime.now()

        pipeline = [
            {"$match": {
                "timestamp": {"$gte": start, "$lte": end},
                "cam_temp": True
            }},
            {"$sort": {"timestamp": -1}},
            {"$group": {
                "_id": "$camera_name",
                "latest_timestamp": {"$first": "$timestamp"},
                "reason": {"$first": "$reason"}
            }},
            {"$project": {
                "alert": "Camera Tampering Detected",
                "reason": {"$concat": ["$reason", " detected"]},
                "camera_name": "$_id",
                "time_elapsed": {
                    "$abs": {
                        "$divide": [
                            {"$subtract": [current_time, "$latest_timestamp"]},
                            1000
                        ]
                    }
                },
                "_id": 0
            }},
            {"$sort": {"camera_name": 1}}
        ]

        results = list(tampering_collection.aggregate(pipeline))
        if not results:
            raise HTTPException(status_code=404, detail="No camera tampering data found")
        for result in results:
            result["time_elapsed"] = self.format_time_elapsed(result["time_elapsed"])
        return [TamperingAlert(**r) for r in results]

router = SafetyMonitoringAPI().router