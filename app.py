
from fastapi import FastAPI
from API.api_main import api_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Store Analytics API",
              description="This is a categorized API for Retail Monitoring",
                version="1.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the API router
app.include_router(api_router)

@app.get("/")
async def root():
    return {"message": "Video Analytics API is running"}