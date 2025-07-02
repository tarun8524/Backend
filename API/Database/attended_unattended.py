from fastapi import FastAPI, APIRouter, HTTPException
from datetime import datetime, time
from pydantic import BaseModel
from typing import List
from API import api_db_handler

collection = api_db_handler.db["attended_unattended"]

class CamerawiseTime(BaseModel):
    camera_name: str
    duration: float

class TimeTrend(BaseModel):
    time: str
    attended_duration: float
    unattended_duration: float

class GetDBdataforAttendance():
    def __init__(self):
        self.router = APIRouter()
        self.router.get("/camerawiseAttendedTime", tags=["Attendance"],
                        response_model=List[CamerawiseTime])(self.get_camerawise_attended_time)
        self.router.get("/camerawiseUnattendedTime", tags=["Attendance"],
                        response_model=List[CamerawiseTime])(self.get_camerawise_unattended_time)
        self.router.get("/attendanceTrend", tags=["Attendance"],
                        response_model=List[TimeTrend])(self.get_attendance_trend)

    def get_camerawise_attended_time(self):
        date_obj = datetime.today().date()
        start = datetime.combine(date_obj, time.min)
        end = datetime.combine(date_obj, time.max)
        pipeline = [
            {"$match": {
                "timestamp": {"$gte": start, "$lte": end},
                "type": "attended"
            }},
            {"$group": {
                "_id": "$camera_name",
                "total_duration": {"$sum": "$time_duration"}
            }},
            {"$sort": {"_id": 1}}
        ]
        results = list(collection.aggregate(pipeline))
        return [CamerawiseTime(camera_name=r["_id"], duration=r["total_duration"]) for r in results]

    def get_camerawise_unattended_time(self):
        date_obj = datetime.today().date()
        start = datetime.combine(date_obj, time.min)
        end = datetime.combine(date_obj, time.max)
        pipeline = [
            {"$match": {
                "timestamp": {"$gte": start, "$lte": end},
                "type": "unattended"
            }},
            {"$group": {
                "_id": "$camera_name",
                "total_duration": {"$sum": "$time_duration"}
            }},
            {"$sort": {"_id": 1}}
        ]
        results = list(collection.aggregate(pipeline))
        return [CamerawiseTime(camera_name=r["_id"], duration=r["total_duration"]) for r in results]

    def get_attendance_trend(self):
        date_obj = datetime.today().date()
        start = datetime.combine(date_obj, time.min)
        end = datetime.combine(date_obj, time.max)
        pipeline = [
            {"$match": {
                "timestamp": {"$gte": start, "$lte": end}
            }},
            {"$project": {
                "hour": {"$hour": "$timestamp"},
                "type": 1,
                "time_duration": 1
            }},
            {"$group": {
                "_id": "$hour",
                "attended_duration": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$type", "attended"]},
                            "$time_duration",
                            0
                        ]
                    }
                },
                "unattended_duration": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$type", "unattended"]},
                            "$time_duration",
                            0
                        ]
                    }
                }
            }},
            {"$sort": {"_id": 1}}
        ]
        results = list(collection.aggregate(pipeline))
        return [
            TimeTrend(
                time=f"{r['_id']:02d}:00",
                attended_duration=r["attended_duration"],
                unattended_duration=r["unattended_duration"]
            ) for r in results
        ]