from fastapi import FastAPI,APIRouter, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient #type:ignore
from datetime import datetime, time
from pydantic import BaseModel  # type: ignore
from typing import List
from collections import defaultdict
from API import api_db_handler

collection = api_db_handler.db["customer_dwell_time"]

router = APIRouter() 
# app = FastAPI()
class CameraWisedwelltime(BaseModel):
    camera_name: str
    duration: float
class Camerawithmax(BaseModel):
    camera_name: str
    duration: float
class Dwelltimetrend(BaseModel):
    time: str
    duration : float

class GetDBdatafordwelltime:
    def __init__(self):
        self.router = APIRouter()
        self.router.get("/CameraWisedwelltime", tags= ["Dwell Time"],
                        response_model=List[CameraWisedwelltime])(self.get_camera_wise_dwelltime)
        # self.router.get("/Maxoccupancy",response_model=Maxoccupancy)(self.get_Maxoccupancy)
        self.router.get("/MaxDwellTime", tags= ["Dwell Time"],
                        response_model = Camerawithmax)(self.get_max_dwelltime)
        self.router.get("/DwellTimeTrend", tags= ["Dwell Time"],
                        response_model = List[Dwelltimetrend])(self.get_dwell_time_trend)

    def get_camera_wise_dwelltime(self):
        today = datetime.today().date()
        start = datetime.combine(today, time.min)
        end = datetime.combine(today, time.max)

        pipeline = [
            {"$match": {"timestamp": {"$gte": start, "$lte": end}}},
            {"$group": {
                "_id": "$camera_name",
                "count": {"$sum": "$customer_dwell_time"}
            }}
        ]
        result = list(collection.aggregate(pipeline))
        return [CameraWisedwelltime(camera_name=r["_id"], duration=float(r["count"])) for r in result]



    
    def get_max_dwelltime(self):
        today = datetime.today().date()
        start = datetime.combine(today, time.min)
        end = datetime.combine(today, time.max)

        pipeline = [
            {"$match": {"timestamp": {"$gte": start, "$lte": end}}},
            {"$sort": {"customer_dwell_time": -1}},
            {"$limit": 1}
        ]
        result = list(collection.aggregate(pipeline))
        if result:
            record = result[0]
            return Camerawithmax(camera_name=record["camera_name"], duration=float(record["customer_dwell_time"]))
        return Camerawithmax(camera_name="", duration=0.0)

    def get_dwell_time_trend(self):
        today = datetime.today().date()
        start = datetime.combine(today, time.min)
        end = datetime.combine(today, time.max)

        pipeline = [
            {"$match": {"timestamp": {"$gte": start, "$lte": end}}},
            {"$group": {
                "_id": {"hour": {"$hour": "$timestamp"}},
                "total_dwell_time": {"$sum": "$customer_dwell_time"}
            }},
            {"$sort": {"_id.hour": 1}}
        ]
        result = list(collection.aggregate(pipeline))
        return [Dwelltimetrend(time=str(r["_id"]["hour"]), duration=float(r["total_dwell_time"])) for r in result]