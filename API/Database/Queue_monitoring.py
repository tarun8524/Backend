from fastapi import FastAPI, APIRouter, HTTPException
from datetime import datetime, time
from pydantic import BaseModel
from typing import List
from API import api_db_handler

collection = api_db_handler.db["billing_counter"]

router = APIRouter()

class CameraLatestCount(BaseModel):
    camera_name: str
    total_length: int
    waiting_time: int

class HourlyTrend(BaseModel):
    time: str
    total_length: int
    waiting_time: int

class QueueMonitoringAPI:
    def __init__(self):
        self.router = APIRouter()
        self.router.get(
            "/camera-latest-count",
            tags=["Queue Monitoring"],
            response_model=List[CameraLatestCount]
        )(self.get_camera_latest_count)
        self.router.get(
            "/camera-hourly-trend/{camera_name}",
            tags=["Queue Monitoring"],
            response_model=List[HourlyTrend]
        )(self.get_camera_hourly_trend)

    def get_camera_latest_count(self):
        date_obj = datetime.today().date()
        start = datetime.combine(date_obj, time.min)
        end = datetime.combine(date_obj, time.max)

        pipeline = [
            {"$match": {
                "timestamp": {"$gte": start, "$lte": end}
            }},
            {"$sort": {"timestamp": -1}},
            {"$group": {
                "_id": "$camera_name",
                "latest_count": {"$first": "$person_count"},
                "latest_timestamp": {"$first": "$timestamp"}
            }},
            {"$project": {
                "camera_name": "$_id",
                "total_length": "$latest_count",
                "waiting_time": {"$multiply": ["$latest_count", 3]},
                "_id": 0
            }},
            {"$sort": {"camera_name": 1}}
        ]

        results = list(collection.aggregate(pipeline))
        return [CameraLatestCount(**r) for r in results]

    def get_camera_hourly_trend(self, camera_name: str):
        date_obj = datetime.today().date()
        start = datetime.combine(date_obj, time.min)
        end = datetime.combine(date_obj, time.max)

        pipeline = [
            {"$match": {
                "timestamp": {"$gte": start, "$lte": end},
                "camera_name": camera_name
            }},
            {"$group": {
                "_id": {"$hour": "$timestamp"},
                "total_count": {"$sum": "$person_count"},
                "avg_count": {"$avg": "$person_count"}
            }},
            {"$sort": {"_id": 1}},
            {"$project": {
                "time": {"$concat": [
                    {"$toString": "$_id"},
                    ":00"
                ]},
                "total_length": "$total_count",
                "waiting_time": {"$multiply": [{"$round": ["$avg_count", 0]}, 3]},
                "_id": 0
            }}
        ]

        results = list(collection.aggregate(pipeline))
        if not results:
            raise HTTPException(status_code=404, detail=f"No data found for camera {camera_name}")
        return [HourlyTrend(**r) for r in results]

router = QueueMonitoringAPI().router