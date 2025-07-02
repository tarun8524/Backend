from fastapi import FastAPI,APIRouter, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient #type: ignore
from datetime import datetime, time
from pydantic import BaseModel  # type: ignore
from typing import List
from collections import defaultdict
from API import api_db_handler

collection = api_db_handler.db["customer_staff"]

router = APIRouter() 
# app = FastAPI()
class CameraWisecustomer_staff_ratio(BaseModel):
    camera_name: str
    customer_count: int
    staff_count: int
class Totalcustomer_staff_ratio(BaseModel):
    customer_count: int
    staff_count: int
class customer_staff_ratiotrend(BaseModel):
    time: str
    customer_count: int
    staff_count: int

class GetDBdataforCustomerStaffRatio():
    def __init__(self):
        self.router = APIRouter()
        self.router.get("/CameraWisecustomerstaffRatio", tags=["Customer Staff Ratio"],
                        response_model=List[CameraWisecustomer_staff_ratio])(self.get_camera_wise)
        self.router.get("/TotalcustomerstaffRatio", tags=["Customer Staff Ratio"],
                        response_model=Totalcustomer_staff_ratio)(self.get_total)
        self.router.get("/CustomerStaffTrend", tags=["Customer Staff Ratio"],
                        response_model=List[customer_staff_ratiotrend])(self.get_trend)

    def get_camera_wise(self):
        today = datetime.today().date()
        start = datetime.combine(today, time.min)
        end = datetime.combine(today, time.max)

        pipeline = [
            {"$match": {"timestamp": {"$gte": start, "$lte": end}}},
            {"$group": {
                "_id": "$camera_name",
                "customer_count": {"$sum": "$customer_count"},
                "staff_count": {"$sum": "$employee_count"}
            }}
        ]

        result = collection.aggregate(pipeline).to_list(None)
        return [CameraWisecustomer_staff_ratio(
                    camera_name=r["_id"],
                    customer_count=r["customer_count"],
                    staff_count=r["staff_count"]
                ) for r in result]

    def get_total(self):
        today = datetime.today().date()
        start = datetime.combine(today, time.min)
        end = datetime.combine(today, time.max)

        pipeline = [
            {"$match": {"timestamp": {"$gte": start, "$lte": end}}},
            {"$group": {
                "_id": None,
                "customer_count": {"$sum": "$customer_count"},
                "staff_count": {"$sum": "$employee_count"}
            }}
        ]

        result = collection.aggregate(pipeline).to_list(1)
        if result:
            data = result[0]
            return Totalcustomer_staff_ratio(
                customer_count=data["customer_count"],
                staff_count=data["staff_count"]
            )
        return Totalcustomer_staff_ratio(customer_count=0, staff_count=0)

    def get_trend(self):
        today = datetime.today().date()
        start = datetime.combine(today, time.min)
        end = datetime.combine(today, time.max)

        pipeline = [
            {"$match": {"timestamp": {"$gte": start, "$lte": end}}},
            {"$group": {
                "_id": {"hour": {"$hour": "$timestamp"}},
                "customer_count": {"$sum": "$customer_count"},
                "staff_count": {"$sum": "$employee_count"}
            }},
            {"$sort": {"_id.hour": 1}}
        ]

        result = collection.aggregate(pipeline).to_list(None)
        return [customer_staff_ratiotrend(
                    time=str(r["_id"]["hour"]),
                    customer_count=r["customer_count"],
                    staff_count=r["staff_count"]
                ) for r in result]