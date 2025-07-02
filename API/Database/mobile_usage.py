from fastapi import FastAPI,APIRouter, HTTPException
from datetime import datetime, time
from pydantic import BaseModel  # type: ignore
from typing import List
from collections import defaultdict
from API import api_db_handler

collection = api_db_handler.db["mobile_usage"]


router = APIRouter()
# app = FastAPI()
class CamerawiseMobileUsage(BaseModel):
    camera_name: str
    duration: float

class Maxoccupancy(BaseModel):
    camera_name: str
    max_count: int

class MobileUsageTrend(BaseModel):
    time : str
    duration : float
    


class GetDBdataforMobileUsage():
    def __init__(self):
        self.router = APIRouter()
        self.router.get("/CamerawiseMobileUsage",tags=["Mobile Usage"],
                        response_model= List[CamerawiseMobileUsage])(self.get_CamerawiseMobileUsage)
        # self.router.get("/Maxoccupancy",response_model=Maxoccupancy)(self.get_Maxoccupancy)
        self.router.get("/MobileUsageTrend",tags=["Mobile Usage"],
                        response_model = List[MobileUsageTrend])(self.get_MobileUsageTrend)

    def get_CamerawiseMobileUsage(self):
        date_obj = datetime.today().date()
        start = datetime.combine(date_obj, time.min)
        end = datetime.combine(date_obj, time.max)

        pipeline = [
            {"$match": {
                "timestamp": {"$gte": start, "$lte": end}
            }},
            {"$group": {
                "_id": "$camera_name",
                "total_duration": {"$sum": "$duration_seconds"}
            }},
            {"$sort": {"total_duration": -1}}
        ]

        results = list(collection.aggregate(pipeline))
        return [CamerawiseMobileUsage(camera_name=r["_id"], duration=r["total_duration"]) for r in results]
    
    # def get_Maxoccupancy(self):
        

    def get_MobileUsageTrend(self):
        date_obj = datetime.today().date()
        start = datetime.combine(date_obj, time.min)
        end = datetime.combine(date_obj, time.max)

        pipeline = [
            {"$match": {
                "timestamp": {"$gte": start, "$lte": end}
            }},
            {"$group": {
                "_id": {"$hour": "$timestamp"},
                "total_duration": {"$sum": "$duration_seconds"}
            }},
            {"$sort": {"_id": 1}}  # sort by hour
        ]

        results = list(collection.aggregate(pipeline))
        return [MobileUsageTrend(time=f"{r['_id']:02d}:00", duration=r["total_duration"]) for r in results]

