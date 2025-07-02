from fastapi import APIRouter
from API.Database.entry_exit import GetDBdataforEntryExit
from API.Database.intrusion import GetDBdataforintrusion
from API.Database.employee_unavalibility import GetDBdataforEmp_unavailability
from API.Database.occupancy_monitoring import GetDBdataforOccupancy_Monitoring
from API.Database.mobile_usage import GetDBdataforMobileUsage
from API.Database.camera_tampering import GetDBdataforCameraTampering
from API.Database.billing_counter import GetDBdataforbillingcounter
from API.Database.customer_staff_ratio import GetDBdataforCustomerStaffRatio
from API.Database.dwell_time import GetDBdatafordwelltime
from API.Database.fall_slip import GetDBdataforfall
from API.Database.billing_alerts import GetDBdataforBillingAlerts
from API.Database.Dashboard import Dashboard
from API.Database.Queue_monitoring import QueueMonitoringAPI
from API.Database.safety import SafetyMonitoringAPI
from API.Database.feedback import FeedbackAPI
from API.Database.attended_unattended import GetDBdataforAttendance
from API.Database.conversion_rate import GetDBdataforBillingEntryExit
from API.Database.shelf_occupancy import GetDBdataforShelfOccupancyAPI
from API.Database.save_cam import CameraDetailsManager


api_router = APIRouter()

# Include all API routers
api_router.include_router(Dashboard().router)
api_router.include_router(GetDBdataforEntryExit().router)
api_router.include_router(GetDBdataforintrusion().router)
api_router.include_router(GetDBdataforEmp_unavailability().router)
api_router.include_router(GetDBdataforOccupancy_Monitoring().router)
api_router.include_router(GetDBdataforMobileUsage().router)
api_router.include_router(GetDBdataforCameraTampering().router)
api_router.include_router(GetDBdataforbillingcounter().router)
api_router.include_router(GetDBdataforCustomerStaffRatio().router)
api_router.include_router(GetDBdatafordwelltime().router)
api_router.include_router(GetDBdataforfall().router)
api_router.include_router(GetDBdataforBillingAlerts().router)
api_router.include_router(GetDBdataforAttendance().router)
api_router.include_router(GetDBdataforBillingEntryExit().router)
api_router.include_router(GetDBdataforShelfOccupancyAPI().router)
api_router.include_router(QueueMonitoringAPI().router)
api_router.include_router(SafetyMonitoringAPI().router)
api_router.include_router(FeedbackAPI().router)
api_router.include_router(CameraDetailsManager().router)