from fastapi import FastAPI,APIRouter, HTTPException
from datetime import datetime, time
from pydantic import BaseModel 
from typing import List
from collections import defaultdict
from API import api_db_handler

collection = api_db_handler.db["emp_unavailability"]

# app = FastAPI()
# from fastapi import APIRouter, Depends
# from datetime import datetime, timedelta
# from pymongo import ASCENDING
# from motor.motor_asyncio import AsyncIOMotorDatabase
# from bson import ObjectId
# from typing import List
# from pydantic import BaseModel

# router = APIRouter()
# app = FastAPI()
class CamerawiseEmp_unavailability(BaseModel):
    camera_name: str
    duration: float

class MostEmp_unavailability(BaseModel):
    camera_name: str
    duration: float

class Emp_unavailabilityTrend(BaseModel):
    time : str
    duration : float


class GetDBdataforEmp_unavailability():
    def __init__(self):
        self.router = APIRouter()
        self.router.get("/camerawiseEmp_unavailability", tags=["Employee Unavailability"],
                        response_model= List[CamerawiseEmp_unavailability])(self.get_camerawiseEmp_unavailability)
        self.router.get("/MostEmp_unavailability", tags=["Employee Unavailability"],
                        response_model=MostEmp_unavailability)(self.get_MostEmp_unavailability)
        self.router.get("/Emp_unavailabilityTrend", tags=["Employee Unavailability"],
                        response_model = List[Emp_unavailabilityTrend])(self.get_Emp_unavailabilityTrend)

    def get_MostEmp_unavailability(self):
        date_obj = datetime.today().date()
        start = datetime.combine(date_obj, time.min)
        end = datetime.combine(date_obj, time.max)
        pipeline = [
            {"$match": {
                "timestamp": {"$gte": start, "$lte": end}
            }},
            {"$group": {
                "_id": "$camera_name",
                "total_unavailability": {"$sum": "$emp_unavailability"}
            }},
            {"$sort": {"total_unavailability": -1}},
            {"$limit": 1}
        ]
        result = list(collection.aggregate(pipeline))
        if result:
            return MostEmp_unavailability(camera_name=result[0]["_id"],duration= round(result[0]["total_unavailability"],2))
            #      {
            #     "camera_name": result[0]["_id"],
            #     "total_unavailability_sec": result[0]["total_unavailability"]
            # }
        else:
            return MostEmp_unavailability(camera_name="Unknown",duration= 0)

    def get_camerawiseEmp_unavailability(self):
        date_obj = datetime.today().date()
        start = datetime.combine(date_obj, time.min)
        end = datetime.combine(date_obj, time.max)
        pipeline = [
            {"$match": {
                "timestamp": {"$gte": start, "$lte": end}
            }},
            {"$group": {
                "_id": "$camera_name",
                "total_unavailability": {"$sum": "$emp_unavailability"}
            }},
            {"$sort": {"_id": 1}}
        ]
        results = collection.aggregate(pipeline)
        return [CamerawiseEmp_unavailability(camera_name= r["_id"], duration = round(r["total_unavailability"],2)) for r in results ] 
        # [
        #     {"camera_name": r["_id"], "total_unavailability_sec": r["total_unavailability"]}
        #     for r in results
        # ]


    def get_Emp_unavailabilityTrend(self):
        date_obj = datetime.today().date()
        start = datetime.combine(date_obj, time.min)
        end = datetime.combine(date_obj, time.max)
        pipeline = [
            {"$match": {
                "timestamp": {"$gte": start, "$lte": end}
            }},
            {"$project": {
                "hour": {"$hour": "$timestamp"},
                "emp_unavailability": 1
            }},
            {"$group": {
                "_id": "$hour",
                "total_unavailability": {"$sum": "$emp_unavailability"}
            }},
            {"$sort": {"_id": 1}}
        ]
        results = collection.aggregate(pipeline)
        return [Emp_unavailabilityTrend(time = f"{r['_id']:02d}:00", duration= round(r["total_unavailability"],2)) for r in results]
        # [
        #     {"hour": f"{r['_id']:02d}:00", "total_unavailability_sec": r["total_unavailability"]}
        #     for r in results
        # ]
