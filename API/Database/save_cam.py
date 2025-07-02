from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from pymongo.errors import OperationFailure #type: ignore
from API import api_db_handler

# Define Pydantic model for camera details
class CameraDetails(BaseModel):
    camera_name: str
    module_names: List[str]
    location: str
    stream_url: str

class CameraDetailsResponse(BaseModel):
    message: str
    inserted_id: str

class CameraDetailsManager:
    def __init__(self):
        self.router = APIRouter(tags=["Camera Details"])  # Initialize router with tags
        self.collection = api_db_handler.db["cam_details"]  # Access MongoDB collection
        # Register the route
        self.router.post("/save-camera", response_model=CameraDetailsResponse)(self.save_camera)

    def save_camera(self, camera: CameraDetails):
        """Save camera details to the 'cam_details' collection."""
        try:
            camera_data = {
                "camera_name": camera.camera_name,
                "module_names": camera.module_names,
                "location": camera.location,
                "stream_url": camera.stream_url
            }
            result = self.collection.insert_one(camera_data)
            return {
                "message": "Camera details saved successfully!",
                "inserted_id": str(result.inserted_id)
            }
        except OperationFailure as e:
            raise HTTPException(status_code=500, detail=f"Failed to save camera details: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error saving camera details: {str(e)}")