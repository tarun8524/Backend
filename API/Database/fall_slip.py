from fastapi import FastAPI, APIRouter, HTTPException
from datetime import datetime, time
from pydantic import BaseModel
from typing import List
from collections import defaultdict
from API import api_db_handler

collection = api_db_handler.db["fall"]

router = APIRouter()

class CamerawiseFall(BaseModel):
    camera_name: str
    count: int

class MaxFall(BaseModel):
    camera_name: str
    count: int

class FallTrend(BaseModel):
    time: str
    count: int

class GetDBdataforfall():
    def __init__(self):
        self.router = APIRouter()
        self.router.get("/camerawise_fall", tags=["Fall"],
                        response_model=List[CamerawiseFall])(self.get_camerawise_fall)
        self.router.get("/max_fall_camera", tags=["Fall"],
                        response_model=MaxFall)(self.get_max_fall_camera)
        self.router.get("/fall_trend", tags=["Fall"],
                        response_model=List[FallTrend])(self.get_fall_trend)

    def get_camerawise_fall(self):
        date_obj = datetime.today().date()
        start = datetime.combine(date_obj, time.min)
        end = datetime.combine(date_obj, time.max)
        pipeline = [
            {"$match": {
                "timestamp": {"$gte": start, "$lte": end},
                "Alert": True
            }},
            {"$group": {
                "_id": "$camera_name",
                "count": {"$sum": 1}
            }}
        ]
        results = collection.aggregate(pipeline)
        return [CamerawiseFall(camera_name=r["_id"], count=r["count"]) for r in results]

    def get_max_fall_camera(self):
        date_obj = datetime.today().date()
        start = datetime.combine(date_obj, time.min)
        end = datetime.combine(date_obj, time.max)
        
        pipeline = [
            {"$match": {
                "timestamp": {"$gte": start, "$lte": end},
                "Alert": True
            }},
            {"$group": {
                "_id": "$camera_name",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}},
            {"$limit": 1}
        ]
        result = list(collection.aggregate(pipeline))
        if result:
            return MaxFall(camera_name=result[0]["_id"], count=result[0]["count"])
        else:
            return MaxFall(camera_name="Unknown", count=0)

    def get_fall_trend(self):
        date_obj = datetime.today().date()
        start = datetime.combine(date_obj, time.min)
        end = datetime.combine(date_obj, time.max)
        pipeline = [
            {"$match": {
                "timestamp": {"$gte": start, "$lte": end},
                "Alert": True
            }},
            {"$project": {
                "hour": {"$hour": "$timestamp"}
            }},
            {"$group": {
                "_id": "$hour",
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}}
        ]
        results = collection.aggregate(pipeline)
        return [FallTrend(time=f"{r['_id']:02d}", count=r["count"]) for r in results]