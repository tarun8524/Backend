from fastapi import FastAPI, APIRouter, HTTPException
from datetime import datetime, time
from pydantic import BaseModel
from typing import List
from API import api_db_handler

collection = api_db_handler.db["shelf_occupancy"]

class CameraShelfData(BaseModel):
    camera_name: str
    shelves: int
    empty_shelves: int
    avg_empty_space: float

class LatestTimestamp(BaseModel):
    timestamp: datetime

class GetDBdataforShelfOccupancyAPI():
    def __init__(self):
        self.router = APIRouter()
        self.router.get("/latestCameraShelfData", tags=["ShelfOccupancy"],
                        response_model=List[CameraShelfData])(self.get_latest_camera_shelf_data)
        self.router.get("/latestTimestamp", tags=["ShelfOccupancy"],
                        response_model=LatestTimestamp)(self.get_latest_timestamp)

    def get_latest_camera_shelf_data(self):
        date_obj = datetime.today().date()
        start = datetime.combine(date_obj, time.min)
        end = datetime.combine(date_obj, time.max)
        # First, find the latest timestamp across all records
        latest_timestamp_pipeline = [
            {"$match": {
                "timestamp": {"$gte": start, "$lte": end}
            }},
            {"$sort": {"timestamp": -1}},
            {"$limit": 1},
            {"$project": {"timestamp": 1}}
        ]
        latest_timestamp_result = list(collection.aggregate(latest_timestamp_pipeline))
        if not latest_timestamp_result:
            raise HTTPException(status_code=404, detail="No data found for today")
        latest_timestamp = latest_timestamp_result[0]["timestamp"]
        
        # Then, get the latest record for each camera at or before this timestamp
        pipeline = [
            {"$match": {
                "timestamp": {"$gte": start, "$lte": latest_timestamp}
            }},
            {"$sort": {"timestamp": -1}},
            {"$group": {
                "_id": "$camera_name",
                "shelves": {"$first": "$shelves"},
                "empty_shelves": {"$first": "$empty_shelves"},
                "avg_empty_space": {"$first": "$avg_empty_space"}
            }},
            {"$sort": {"_id": 1}}
        ]
        results = list(collection.aggregate(pipeline))
        if not results:
            raise HTTPException(status_code=404, detail="No camera data found for the latest timestamp")
        return [
            CameraShelfData(
                camera_name=r["_id"],
                shelves=r["shelves"],
                empty_shelves=r["empty_shelves"],
                avg_empty_space=r["avg_empty_space"]
            ) for r in results
        ]

    def get_latest_timestamp(self):
        date_obj = datetime.today().date()
        start = datetime.combine(date_obj, time.min)
        end = datetime.combine(date_obj, time.max)
        pipeline = [
            {"$match": {
                "timestamp": {"$gte": start, "$lte": end}
            }},
            {"$sort": {"timestamp": -1}},
            {"$limit": 1},
            {"$project": {"timestamp": 1}}
        ]
        result = list(collection.aggregate(pipeline))
        if not result:
            raise HTTPException(status_code=404, detail="No timestamp data found for today")
        return LatestTimestamp(timestamp=result[0]["timestamp"])