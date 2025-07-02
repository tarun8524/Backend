from fastapi import FastAPI, APIRouter
from datetime import datetime, time
from pydantic import BaseModel
from typing import List
from API import api_db_handler

billing_collection = api_db_handler.db["billing_count"]
entry_exit_collection = api_db_handler.db["entry_exit"]

class CamerawiseBilling(BaseModel):
    camera_name: str
    billing_count: int

class HourlyEntryTrend(BaseModel):
    time: str
    entry_count: int

class HourlyConversionRate(BaseModel):
    time: str
    conversion_rate: float

class GetDBdataforBillingEntryExit():
    def __init__(self):
        self.router = APIRouter()
        self.router.get("/camerawiseBillingCount", tags=["BillingEntryExit"],
                        response_model=List[CamerawiseBilling])(self.get_camerawise_billing_count)
        self.router.get("/hourlyEntryTrend", tags=["BillingEntryExit"],
                        response_model=List[HourlyEntryTrend])(self.get_hourly_entry_trend)
        self.router.get("/hourlyConversionRate", tags=["BillingEntryExit"],
                        response_model=List[HourlyConversionRate])(self.get_hourly_conversion_rate)

    def get_camerawise_billing_count(self):
        date_obj = datetime.today().date()
        start = datetime.combine(date_obj, time.min)
        end = datetime.combine(date_obj, time.max)
        pipeline = [
            {"$match": {
                "timestamp": {"$gte": start, "$lte": end}
            }},
            {"$group": {
                "_id": "$camera_name",
                "total_billing_count": {"$sum": "$billing_count"}
            }},
            {"$sort": {"_id": 1}}
        ]
        results = list(billing_collection.aggregate(pipeline))
        return [CamerawiseBilling(camera_name=r["_id"], billing_count=r["total_billing_count"]) for r in results]

    def get_hourly_entry_trend(self):
        date_obj = datetime.today().date()
        start = datetime.combine(date_obj, time.min)
        end = datetime.combine(date_obj, time.max)
        pipeline = [
            {"$match": {
                "timestamp": {"$gte": start, "$lte": end}
            }},
            {"$project": {
                "hour": {"$hour": "$timestamp"},
                "entry_count": 1
            }},
            {"$group": {
                "_id": "$hour",
                "total_entry_count": {"$sum": "$entry_count"}
            }},
            {"$sort": {"_id": 1}}
        ]
        results = list(entry_exit_collection.aggregate(pipeline))
        return [
            HourlyEntryTrend(
                time=f"{r['_id']:02d}:00",
                entry_count=r["total_entry_count"]
            ) for r in results
        ]

    def get_hourly_conversion_rate(self):
        date_obj = datetime.today().date()
        start = datetime.combine(date_obj, time.min)
        end = datetime.combine(date_obj, time.max)
        
        # Get billing counts by hour
        billing_pipeline = [
            {"$match": {
                "timestamp": {"$gte": start, "$lte": end}
            }},
            {"$project": {
                "hour": {"$hour": "$timestamp"},
                "billing_count": 1
            }},
            {"$group": {
                "_id": "$hour",
                "total_billing": {"$sum": "$billing_count"}
            }}
        ]
        
        # Get total visitors (entry_count only) by hour
        visitor_pipeline = [
            {"$match": {
                "timestamp": {"$gte": start, "$lte": end}
            }},
            {"$project": {
                "hour": {"$hour": "$timestamp"},
                "entry_count": 1
            }},
            {"$group": {
                "_id": "$hour",
                "total_visitors": {"$sum": "$entry_count"}
            }}
        ]
        
        billing_results = {r["_id"]: r["total_billing"] for r in billing_collection.aggregate(billing_pipeline)}
        visitor_results = {r["_id"]: r["total_visitors"] for r in entry_exit_collection.aggregate(visitor_pipeline)}
        
        # Only include hours where either billing or visitor data exists
        hours = set(billing_results.keys()) | set(visitor_results.keys())
        results = []
        for hour in sorted(hours):
            billings = billing_results.get(hour, 0)
            visitors = visitor_results.get(hour, 0)
            conversion_rate = (billings / visitors * 100) if visitors > 0 else 0.0
            results.append(HourlyConversionRate(
                time=f"{hour:02d}:00",
                conversion_rate=round(conversion_rate, 2)
            ))
        
        return results