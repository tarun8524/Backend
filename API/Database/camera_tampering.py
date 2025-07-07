from fastapi import FastAPI, APIRouter, HTTPException
from datetime import datetime, time
from pydantic import BaseModel
from typing import List
from collections import defaultdict
from API import api_db_handler

collection = api_db_handler.db["camera_tempering"]

router = APIRouter()

class CameraWiseTempering(BaseModel):
    camera_name: str
    total: int

class CameraTemperingReason(BaseModel):
    camera_name: str
    reason: str
    count: int
    
class GetDBdataforCameraTampering():
    def __init__(self):
        self.router = APIRouter()
        self.router.get("/CameraWiseTempering", tags=["Camera Tampering"],
                        response_model=List[CameraWiseTempering])(self.get_CameraWiseTempering)
        self.router.get("/CameraTemperingReason", tags=["Camera Tampering"],
                        response_model=List[CameraTemperingReason])(self.get_CameraTemperingReason)

    def get_CameraWiseTempering(self):
        date_obj = datetime.today().date()
        start = datetime.combine(date_obj, time.min)
        end = datetime.combine(date_obj, time.max)
        pipeline = [
            {"$match": {
                "timestamp": {"$gte": start, "$lte": end}
            }},
            {"$group": {
                "_id": "$camera_name",
                "total": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}}
        ]
        results = list(collection.aggregate(pipeline))
        return [CameraWiseTempering(camera_name=r["_id"], total=r["total"]) for r in results]
    
    def get_CameraTemperingReason(self):
        date_obj = datetime.today().date()
        start = datetime.combine(date_obj, time.min)
        end = datetime.combine(date_obj, time.max)
        pipeline = [
            {"$match": {
                "timestamp": {"$gte": start, "$lte": end}
            }},
            {"$group": {
                "_id": {
                    "camera_name": "$camera_name",
                    "reason": "$reason"
                },
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id.camera_name": 1, "_id.reason": 1}}
        ]
        results = list(collection.aggregate(pipeline))
        return [
            CameraTemperingReason(
                camera_name=r["_id"]["camera_name"],
                reason=r["_id"]["reason"],
                count=r["count"]
            )
            for r in results
        ]