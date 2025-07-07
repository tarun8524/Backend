from fastapi import FastAPI, APIRouter, HTTPException
from datetime import datetime, time, timedelta
from pydantic import BaseModel
from typing import List, Union
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
    timestamp: datetime

class FallAlert(BaseModel):
    alert: str = "Fall Detected"
    reason: str = "Person fall/slip Detected"
    camera_name: str
    time_elapsed: str
    timestamp: datetime

class TamperingAlert(BaseModel):
    alert: str = "Camera Tampering Detected"
    reason: str
    camera_name: str
    time_elapsed: str
    timestamp: datetime

class RespondRequest(BaseModel):
    alert: str
    reason: str
    camera_name: str
    timestamp: datetime

class SafetyMonitoringAPI:
    def __init__(self):
        self.router = APIRouter()
        self.router.get(
            "/latest-safety-alerts",
            tags=["Safety Monitoring"],
            response_model=List[Union[IntrusionAlert, FallAlert, TamperingAlert]]
        )(self.get_latest_safety_alerts)
        self.router.post(
            "/respond",
            tags=["Safety Monitoring"],
            response_model=dict
        )(self.respond_to_alert)

    def format_time_elapsed(self, seconds):
        seconds = abs(seconds)
        if seconds < 60:
            return f"{int(seconds)} seconds"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{int(minutes)} minutes"
        else:
            hours = seconds // 3600
            return f"{int(hours)} hours"

    def get_latest_safety_alerts(self):
        date_obj = datetime.today().date()
        start = datetime.combine(date_obj, time.min)
        end = datetime.combine(date_obj, time.max)
        current_time = datetime.now()

        # Intrusion pipeline
        intrusion_pipeline = [
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
                "timestamp": "$latest_timestamp",
                "time_elapsed": {
                    "$abs": {
                        "$divide": [
                            {"$subtract": [current_time, "$latest_timestamp"]},
                            1000
                        ]
                    }
                },
                "_id": 0
            }}
        ]

        # Fall pipeline
        fall_pipeline = [
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
                "timestamp": "$latest_timestamp",
                "time_elapsed": {
                    "$abs": {
                        "$divide": [
                            {"$subtract": [current_time, "$latest_timestamp"]},
                            1000
                        ]
                    }
                },
                "_id": 0
            }}
        ]

        # Tampering pipeline
        tampering_pipeline = [
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
                "timestamp": "$latest_timestamp",
                "time_elapsed": {
                    "$abs": {
                        "$divide": [
                            {"$subtract": [current_time, "$latest_timestamp"]},
                            1000
                        ]
                    }
                },
                "_id": 0
            }}
        ]

        results = []
        
        # Execute all pipelines
        intrusion_results = list(intrusion_collection.aggregate(intrusion_pipeline))
        for result in intrusion_results:
            result["time_elapsed"] = self.format_time_elapsed(result["time_elapsed"])
            results.append(IntrusionAlert(**result))

        fall_results = list(fall_collection.aggregate(fall_pipeline))
        for result in fall_results:
            result["time_elapsed"] = self.format_time_elapsed(result["time_elapsed"])
            results.append(FallAlert(**result))

        tampering_results = list(tampering_collection.aggregate(tampering_pipeline))
        for result in tampering_results:
            result["time_elapsed"] = self.format_time_elapsed(result["time_elapsed"])
            results.append(TamperingAlert(**result))

        if not results:
            raise HTTPException(status_code=404, detail="No safety alerts found")

        # Sort all results by camera_name
        results.sort(key=lambda x: x.camera_name)
        return results

    def respond_to_alert(self, request: RespondRequest):
        date_obj = datetime.today().date()
        start = datetime.combine(date_obj, time.min)
        end = datetime.combine(date_obj, time.max)

        if request.alert == "Intrusion Alert":
            result = intrusion_collection.update_one(
                {
                    "camera_name": request.camera_name,
                    "timestamp": {"$gte": start, "$lte": end, "$gte": request.timestamp - timedelta(seconds=1), "$lte": request.timestamp + timedelta(seconds=1)},
                    "intrusion": True
                },
                {"$set": {"intrusion": False}}
            )
            if result.matched_count == 0:
                raise HTTPException(status_code=404, detail="Intrusion alert not found")
            return {"message": f"Intrusion alert for {request.camera_name} marked as responded"}

        elif request.alert == "Fall Detected":
            result = fall_collection.update_one(
                {
                    "camera_name": request.camera_name,
                    "timestamp": {"$gte": start, "$lte": end, "$gte": request.timestamp - timedelta(seconds=1), "$lte": request.timestamp + timedelta(seconds=1)},
                    "Alert": True
                },
                {"$set": {"Alert": False}}
            )
            if result.matched_count == 0:
                raise HTTPException(status_code=404, detail="Fall alert not found")
            return {"message": f"Fall alert for {request.camera_name} marked as responded"}

        elif request.alert == "Camera Tampering Detected":
            # Remove " detected" suffix from reason for matching
            db_reason = request.reason.replace(" detected", "")
            result = tampering_collection.update_one(
                {
                    "camera_name": request.camera_name,
                    "reason": db_reason,
                    "timestamp": {"$gte": start, "$lte": end, "$gte": request.timestamp - timedelta(seconds=1), "$lte": request.timestamp + timedelta(seconds=1)},
                    "cam_temp": True
                },
                {"$set": {"cam_temp": False}}
            )
            if result.matched_count == 0:
                raise HTTPException(status_code=404, detail="Tampering alert not found")
            return {"message": f"Tampering alert for {request.camera_name} marked as responded"}

        else:
            raise HTTPException(status_code=400, detail="Invalid alert type")

router = SafetyMonitoringAPI().router