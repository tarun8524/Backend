from fastapi import APIRouter, HTTPException
from datetime import datetime, time
from pydantic import BaseModel 
from typing import List
from collections import defaultdict
from API import api_db_handler
# from dbcollection import MongoDBHandler

# Database_Mongoclient = MongoDBHandler()
# database = Database_Mongoclient
collection = api_db_handler.db['entry_exit']
# app = FastAPI()

class TotalEntryExit(BaseModel):
    total_entry: int
    total_exit : int
class PeakEntryExit(BaseModel):
    peak_hour : str
    peak_entry: int
    peak_exit : int
class EntryExitTrend(BaseModel):
    time: str
    entry: int
    exit : int



class GetDBdataforEntryExit():
    def __init__(self):
        self.router = APIRouter()
        self.router.get("/total_entry_exit", tags=["Entry_exit"],
                        response_model = TotalEntryExit)(self.get_total_entry_exit)
        self.router.get("/peak_entry_exit", tags=["Entry_exit"],
                        response_model=PeakEntryExit)(self.get_peak_entry_exit)
        self.router.get("/entry_exit_trend", tags=["Entry_exit"],
                        response_model=List[EntryExitTrend])(self.get_entry_exit_trend)
    
    def get_total_entry_exit(self):
        date_obj = datetime.today().date()
        start = datetime.combine(date_obj, time.min)
        end = datetime.combine(date_obj, time.max)
        try:
            datas= collection.find({
                "timestamp": {"$gte": start,"$lte": end}})
            total_entry = 0
            total_exit = 0

            for doc in datas:
                total_entry += doc.get("entry_count", 0)
                total_exit += doc.get("exit_count", 0)

            return TotalEntryExit(total_entry=total_entry, total_exit=total_exit)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


    
    def get_peak_entry_exit(self):
        date_obj = datetime.today().date()
        start = datetime.combine(date_obj, time.min)
        end = datetime.combine(date_obj, time.max)
        try:
            datas = collection.find({"timestamp": {"$gte": start, "$lte": end}})
            hourly_data = defaultdict(lambda: {"entry": 0, "exit": 0})

            for doc in datas:
                timestamp = doc.get("timestamp")
                if not timestamp:
                    continue
                hour = timestamp.strftime("%H:00")  # format hour e.g. "14:00"
                hourly_data[hour]["entry"] += doc.get("entry_count", 0)
                hourly_data[hour]["exit"] += doc.get("exit_count", 0)

            # Find hour with highest combined entry+exit
            peak_hour, peak_data = max(hourly_data.items(), key=lambda x: x[1]["entry"] + x[1]["exit"])

            return PeakEntryExit(
                peak_hour=peak_hour,
                peak_entry=peak_data["entry"],
                peak_exit=peak_data["exit"]
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        
    
    def get_entry_exit_trend(self):
        date_obj = datetime.today().date()
        start = datetime.combine(date_obj, time.min)
        end = datetime.combine(date_obj, time.max)

        # MongoDB aggregation pipeline: group by hour
        pipeline = [
            {
                "$match": {
                    "timestamp": {"$gte": start, "$lte": end}
                }
            },
            {
                "$group": {
                    "_id": {"$hour": "$timestamp"},
                    "total_entry": {"$sum": "$entry_count"},
                    "total_exit": {"$sum": "$exit_count"}
                }
            },
            {
                "$sort": {"_id": 1}
            }
        ]
        try:
            results = collection.aggregate(pipeline)
            print(results)
            trends = []
            for doc in results:
                hour = doc["_id"]
                time_label = f"{hour:02d}:00"
                trends.append(
                    EntryExitTrend(
                        time=time_label,
                        entry=doc["total_entry"],
                        exit=doc["total_exit"]
                    )
                )

            return trends
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))   

