from fastapi import FastAPI,APIRouter, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient #type: ignore
from datetime import datetime, time
from pydantic import BaseModel  # type: ignore
from typing import List
from collections import defaultdict
from API import api_db_handler

collection = api_db_handler.db["billing_counter"]

router = APIRouter() 
# app = FastAPI()
class CameraWisebilling(BaseModel):
    camera_name: str
    count: int
class Totalbilling(BaseModel):
    count: int
class Billingcountertrend(BaseModel):
    time: str
    count : int

class GetDBdataforbillingcounter():
    def __init__(self):
        self.router = APIRouter()
        self.router.get("/CameraWisebilling", tags= ["Billing Counter"],
                        response_model= List[CameraWisebilling])(self.get_CameraWisebilling)
        # self.router.get("/Maxoccupancy",response_model=Maxoccupancy)(self.get_Maxoccupancy)
        self.router.get("/Totalbillingcount", tags= ["Billing Counter"],
                        response_model = Totalbilling)(self.get_Totalbilling)
        self.router.get('/BillingCounterTrend', tags = ["Billing Counter"],
                        response_model= List[Billingcountertrend])(self.get_billingtrend)
    def get_CameraWisebilling(self):
        date_obj = datetime.today().date()
        start = datetime.combine(date_obj, time.min)
        end = datetime.combine(date_obj, time.max)
        pipeline = [
                {"$match": {"timestamp": {"$gte": start, "$lte": end}}},
                {"$group": {
                    "_id": "$camera_name",
                    "total": {"$sum": "$person_count"}
                }}
            ]
        result = collection.aggregate(pipeline).to_list(length=None)
        return [CameraWisebilling(camera_name=r["_id"], count=r["total"]) for r in result]
    
    def get_Totalbilling(self):
        today = datetime.today().date()
        start = datetime.combine(today, time.min)
        end = datetime.combine(today, time.max)

        pipeline = [
            {"$match": {"timestamp": {"$gte": start, "$lte": end}}},
            {"$group": {
                "_id": None,
                "total": {"$sum": "$person_count"}
            }}
        ]
        result = collection.aggregate(pipeline).to_list(1)
        total = result[0]["total"] if result else 0
        return Totalbilling(count= total)
    
    def get_billingtrend(self):
        today = datetime.today().date()
        start = datetime.combine(today, time.min)
        end = datetime.combine(today, time.max)

        pipeline = [
            {"$match": {"timestamp": {"$gte": start, "$lte": end}}},
            {"$group": {
                "_id": {
                    "hour": {"$hour": "$timestamp"}
                },
                "person_count": {"$sum": "$person_count"}
            }},
            {"$sort": {"_id.hour": 1}}
        ]
        result = collection.aggregate(pipeline).to_list(None)
        return [Billingcountertrend(time=str(r["_id"]["hour"]), count= r["person_count"]) for r in result]
           