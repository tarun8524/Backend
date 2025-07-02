from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import List
from API import api_db_handler
from enum import Enum

customer_staff_collection = api_db_handler.db["customer_staff"]
dwell_time_collection = api_db_handler.db["customer_dwell_time"]
entry_exit_collection = api_db_handler.db["entry_exit"]
billing_count_collection = api_db_handler.db["billing_count"]

class TimeRange(str, Enum):
    LAST_24_HOURS = "24hr"
    LAST_7_DAYS = "7d"
    LAST_30_DAYS = "30d"
    LAST_90_DAYS = "90d"

class CamerawiseCustomerCount(BaseModel):
    camera_name: str
    customer_count: int

class DwellTimeResponse(BaseModel):
    average_dwell_time: float


class TotalEntryVisitorsResponse(BaseModel):
    total_entry_visitors: int

class ConversionRateResponse(BaseModel):
    conversion_rate: float
    total_billing_count: int

class TimeRangeRequest(BaseModel):
    time_range: TimeRange

class Dashboard:
    def __init__(self):
        self.router = APIRouter()
        self.current_time_range = TimeRange.LAST_24_HOURS  # Default time range
        
        # Endpoint to set time range
        self.router.post(
            "/set_time_range",
            tags=["Dashboard"],
            response_model=dict
        )(self.set_time_range)
        
        # Endpoint for camerawise customer count
        self.router.get(
            "/camerawise_customer_count",
            tags=["Dashboard"],
            response_model=List[CamerawiseCustomerCount]
        )(self.get_camerawise_customer_count)
        
        
        # Endpoint for average dwell time
        self.router.get(
            "/average_dwell_time",
            tags=["Dashboard"],
            response_model=DwellTimeResponse
        )(self.get_average_dwell_time)
        
        # Endpoint for total entry visitors
        self.router.get(
            "/total_entry_visitors",
            tags=["Dashboard"],
            response_model=TotalEntryVisitorsResponse
        )(self.get_total_entry_visitors)
        
        # Endpoint for conversion rate
        self.router.get(
            "/conversion_rate",
            tags=["Dashboard"],
            response_model=ConversionRateResponse
        )(self.get_conversion_rate)

    async def set_time_range(self, request: TimeRangeRequest):
        self.current_time_range = request.time_range
        return {"message": f"Time range set to {self.current_time_range}"}

    def _get_time_range(self) -> tuple[datetime, datetime]:
        end = datetime.now()
        if self.current_time_range == TimeRange.LAST_24_HOURS:
            start = end - timedelta(hours=24)
        elif self.current_time_range == TimeRange.LAST_7_DAYS:
            start = end - timedelta(days=7)
        elif self.current_time_range == TimeRange.LAST_30_DAYS:
            start = end - timedelta(days=30)
        else:  # 90d
            start = end - timedelta(days=90)
        return start, end

    async def get_camerawise_customer_count(self):
        start, end = self._get_time_range()
        pipeline = [
            {"$match": {
                "timestamp": {"$gte": start, "$lte": end}
            }},
            {"$group": {
                "_id": "$camera_name",
                "customer_count": {"$sum": "$customer_count"}
            }}
        ]
        results = customer_staff_collection.aggregate(pipeline)
        return [CamerawiseCustomerCount(camera_name=r["_id"], customer_count=r["customer_count"]) for r in results]


    async def get_average_dwell_time(self):
        start, end = self._get_time_range()
        pipeline = [
            {"$match": {
                "timestamp": {"$gte": start, "$lte": end}
            }},
            {"$group": {
                "_id": None,
                "average_dwell_time": {"$avg": "$customer_dwell_time"}
            }}
        ]
        result = dwell_time_collection.aggregate(pipeline)
        avg_dwell = round(next(result, {"average_dwell_time": 0})["average_dwell_time"], 2)
        return DwellTimeResponse(average_dwell_time=avg_dwell or 0)

    async def get_total_entry_visitors(self):
        start, end = self._get_time_range()
        pipeline = [
            {"$match": {
                "timestamp": {"$gte": start, "$lte": end}
            }},
            {"$group": {
                "_id": None,
                "total_entry_visitors": {"$sum": "$entry_count"}
            }}
        ]
        result = entry_exit_collection.aggregate(pipeline)
        total = next(result, {"total_entry_visitors": 0})["total_entry_visitors"]
        return TotalEntryVisitorsResponse(total_entry_visitors=total)

    async def get_conversion_rate(self):
        start, end = self._get_time_range()
        
        # Get total entry visitors
        entry_pipeline = [
            {"$match": {
                "timestamp": {"$gte": start, "$lte": end}
            }},
            {"$group": {
                "_id": None,
                "total_entry_visitors": {"$sum": "$entry_count"}
            }}
        ]
        entry_result = entry_exit_collection.aggregate(entry_pipeline)
        total_entries = next(entry_result, {"total_entry_visitors": 0})["total_entry_visitors"]
        
        # Get total billing count
        billing_pipeline = [
            {"$match": {
                "timestamp": {"$gte": start, "$lte": end}
            }},
            {"$group": {
                "_id": None,
                "total_billing_count": {"$sum": "$billing_count"}
            }}
        ]
        billing_result = billing_count_collection.aggregate(billing_pipeline)
        total_billing = next(billing_result, {"total_billing_count": 0})["total_billing_count"]
        
        # Calculate conversion rate
        if total_entries > 0:
            conversion_rate = round((total_billing / total_entries) * 100, 2)
        else:
            conversion_rate = 0.0
        
        return ConversionRateResponse(
            conversion_rate=conversion_rate,
            total_billing_count=total_billing
        )