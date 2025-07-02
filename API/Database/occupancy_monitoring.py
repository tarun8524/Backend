from fastapi import FastAPI,APIRouter, HTTPException
from datetime import datetime, time
from pydantic import BaseModel  # type: ignore
from typing import List
from collections import defaultdict
from API import api_db_handler

collection = api_db_handler.db["occupancy_monitoring"]


router = APIRouter()
# app = FastAPI()
class CamerawiseOccupancy(BaseModel):
    camera_name: str
    count: int

class Maxoccupancy(BaseModel):
    camera_name: str
    max_count: int

class OccupancyTrend(BaseModel):
    time : str
    count : int
    


class GetDBdataforOccupancy_Monitoring():
    def __init__(self):
        self.router = APIRouter()
        self.router.get("/CamerawiseOccupancy",tags= ["Occupancy Monitoring"],
                        response_model= List[CamerawiseOccupancy])(self.get_CamerawiseOccupancy)
        self.router.get("/Maxoccupancy",tags= ["Occupancy Monitoring"],
                        response_model=Maxoccupancy)(self.get_Maxoccupancy)
        self.router.get("/OccupancyTrend",tags= ["Occupancy Monitoring"],
                        response_model = List[OccupancyTrend])(self.get_OccupancyTrend)

    def get_CamerawiseOccupancy(self):
        date_obj = datetime.today().date()
        start = datetime.combine(date_obj, time.min)
        end = datetime.combine(date_obj, time.max)

        pipeline = [
            {"$match": {
                "timestamp": {"$gte": start, "$lte": end}
            }},
            {"$group": {
                "_id": "$camera_name",
                "total_person_count": {"$sum": "$person_count"}
            }},
            {"$sort": {"total_person_count": -1}}
        ]

        results = list(collection.aggregate(pipeline))
        return [CamerawiseOccupancy(camera_name=  r["_id"], count = r["total_person_count"]) for r in results]


    def get_Maxoccupancy(self):
        date_obj = datetime.today().date()
        start = datetime.combine(date_obj, time.min)
        end = datetime.combine(date_obj, time.max)

        pipeline = [
            {"$match": {
                "timestamp": {"$gte": start, "$lte": end}
            }},
            {"$group": {
                "_id": "$camera_name",
                "total_person_count": {"$sum": "$person_count"}
            }},
            {"$sort": {"total_person_count": -1}},
            {"$limit": 1}
        ]

        result = list(collection.aggregate(pipeline))
        if result:
            return Maxoccupancy(camera_name=result[0]["_id"], max_count=result[0]["total_person_count"])
        else:
            return Maxoccupancy(camera_name="Unknown", max_count=0)


    def get_OccupancyTrend(self):
        date_obj = datetime.today().date()
        start = datetime.combine(date_obj, time.min)
        end = datetime.combine(date_obj, time.max)

        pipeline = [
            {"$match": {
                "timestamp": {"$gte": start, "$lte": end}
            }},
            {"$group": {
                "_id": {"$hour": "$timestamp"},
                "person_count": {"$sum": "$person_count"}
            }},
            {"$sort": {"_id": 1}}
        ]
        
        results = list(collection.aggregate(pipeline))
        return [OccupancyTrend(time= f"{r['_id']:02d}:00", count = r["person_count"]) for r in results]
