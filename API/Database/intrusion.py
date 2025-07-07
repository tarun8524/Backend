from fastapi import FastAPI, APIRouter, HTTPException
from datetime import datetime, time
from pydantic import BaseModel 
from typing import List
from collections import defaultdict
from API import api_db_handler

collection = api_db_handler.db["intrusion"]

router = APIRouter()

class CamerawiseIntrusion(BaseModel):
    camera_name: str
    count: int

class MaxIntrusion(BaseModel):
    camera_name: str
    count: int

class IntrusionTrend(BaseModel):
    time: str
    count: int

class GetDBdataforintrusion():
    def __init__(self):
        self.router = APIRouter()
        self.router.get("/camerawise_intrusion", tags=["Intrusion"],
                        response_model=List[CamerawiseIntrusion])(self.get_camerawise_intrusion)
        self.router.get("/max_intrusion_camera", tags=["Intrusion"],
                        response_model=MaxIntrusion)(self.get_max_intrusion_camera)
        self.router.get("/intrusion_trend", tags=["Intrusion"],
                        response_model=List[IntrusionTrend])(self.get_intrusion_trend)

    def get_camerawise_intrusion(self):
        date_obj = datetime.today().date()
        start = datetime.combine(date_obj, time.min)
        end = datetime.combine(date_obj, time.max)
        pipeline = [
            {"$match": {
                "timestamp": {"$gte": start, "$lte": end}
            }},
            {"$group": {
                "_id": "$camera_name",
                "count": {"$sum": 1}
            }}
        ]
        results = collection.aggregate(pipeline)
        return [CamerawiseIntrusion(camera_name=r["_id"], count=r["count"]) for r in results]

    def get_max_intrusion_camera(self):
        date_obj = datetime.today().date()
        start = datetime.combine(date_obj, time.min)
        end = datetime.combine(date_obj, time.max)
        
        pipeline = [
            {"$match": {
                "timestamp": {"$gte": start, "$lte": end}
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
            return MaxIntrusion(camera_name=result[0]["_id"], count=result[0]["count"])
        else:
            return MaxIntrusion(camera_name="Unknown", count=0)

    def get_intrusion_trend(self):
        date_obj = datetime.today().date()
        start = datetime.combine(date_obj, time.min)
        end = datetime.combine(date_obj, time.max)
        
        pipeline = [
            {"$match": {
                "timestamp": {"$gte": start, "$lte": end}
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
        return [IntrusionTrend(time=f"{r['_id']:02d}", count=r["count"]) for r in results]