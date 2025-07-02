from fastapi import FastAPI, APIRouter
from datetime import datetime, time
from pydantic import BaseModel
from typing import List
from API import api_db_handler

collection_alerts = api_db_handler.db["billing_alerts"]
collection_billing = api_db_handler.db["billing_count"]

router = APIRouter()

class CameraNoBillAlerts(BaseModel):
    camera_name: str
    count: int

class CameraNoCustomerAlerts(BaseModel):
    camera_name: str
    count: int

class AlertsTrend(BaseModel):
    time: str
    count: int

class BillingCountTrend(BaseModel):
    time: str
    total_billing_count: int

class GetDBdataforBillingAlerts():
    def __init__(self):
        self.router = APIRouter()
        self.router.get("/no_bill_alerts", tags=["Billing Alerts"],
                        response_model=List[CameraNoBillAlerts])(self.get_no_bill_alerts)
        self.router.get("/no_customer_alerts", tags=["Billing Alerts"],
                        response_model=List[CameraNoCustomerAlerts])(self.get_no_customer_alerts)
        self.router.get("/alerts_trend", tags=["Billing Alerts"],
                        response_model=List[AlertsTrend])(self.get_alerts_trend)
        self.router.get("/billing_count_trend", tags=["Billing Alerts"],
                        response_model=List[BillingCountTrend])(self.get_billing_count_trend)

    def get_no_bill_alerts(self):
        date_obj = datetime.today().date()
        start = datetime.combine(date_obj, time.min)
        end = datetime.combine(date_obj, time.max)
        pipeline = [
            {"$match": {
                "timestamp": {"$gte": start, "$lte": end},
                "alerts": True,
                "reason": "Customer Present but No Bill Printed"
            }},
            {"$group": {
                "_id": "$camera_name",
                "count": {"$sum": 1}
            }}
        ]
        results = collection_alerts.aggregate(pipeline)
        return [CameraNoBillAlerts(camera_name=r["_id"], count=r["count"]) for r in results]

    def get_no_customer_alerts(self):
        date_obj = datetime.today().date()
        start = datetime.combine(date_obj, time.min)
        end = datetime.combine(date_obj, time.max)
        pipeline = [
            {"$match": {
                "timestamp": {"$gte": start, "$lte": end},
                "alerts": True,
                "reason": "Bill Printed but Customer Not Present"
            }},
            {"$group": {
                "_id": "$camera_name",
                "count": {"$sum": 1}
            }}
        ]
        results = collection_alerts.aggregate(pipeline)
        return [CameraNoCustomerAlerts(camera_name=r["_id"], count=r["count"]) for r in results]

    def get_alerts_trend(self):
        date_obj = datetime.today().date()
        start = datetime.combine(date_obj, time.min)
        end = datetime.combine(date_obj, time.max)
        pipeline = [
            {"$match": {
                "timestamp": {"$gte": start, "$lte": end},
                "alerts": True
            }},
            {"$project": {
                "hour": {"$hour": "$timestamp"}
            }},
            {"$group": {
                "_id": "$hour",
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}}
        ]
        results = collection_alerts.aggregate(pipeline)
        return [AlertsTrend(time=f"{r['_id']:02d}", count=r["count"]) for r in results]

    def get_billing_count_trend(self):
        date_obj = datetime.today().date()
        start = datetime.combine(date_obj, time.min)
        end = datetime.combine(date_obj, time.max)
        pipeline = [
            {"$match": {
                "timestamp": {"$gte": start, "$lte": end}
            }},
            {"$project": {
                "hour": {"$hour": "$timestamp"},
                "billing_count": 1
            }},
            {"$group": {
                "_id": "$hour",
                "total_billing_count": {"$sum": "$billing_count"}
            }},
            {"$sort": {"_id": 1}}
        ]
        results = collection_billing.aggregate(pipeline)
        results_list = list(results)
        return [BillingCountTrend(time=f"{r['_id']:02d}", total_billing_count=r["total_billing_count"]) for r in results_list]