from datetime import datetime, timezone

from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(
    title="KinTraffic API",
    description="Intelligent traffic management platform for Kinshasa",
    version="0.1.0",
)

class TrafficObservation(BaseModel):
    intersection_id: int
    vehicle_count: int = Field(ge=0)
    average_speed: float = Field(ge=0)
    congestion_level: str

intersections_data = [
    {
        "id": 1,
        "name": "Rond-point Victoire",
        "city": "Kinshasa"
    },
    {
        "id": 2,
        "name": "Rond-point Ngaba",
        "city": "Kinshasa"
    }
]

traffic_data = []

@app.get("/")
def home():
    return {
        "project": "KinTraffic",
        "version": "0.1.0",
        "status": "online",
        "city": "Kinshasa",
        "message": "KinTraffic API is running"
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc)
    }

@app.get("/intersections")
def get_intersections():
    return intersections_data

@app.get("/traffic")
def get_traffic():
    return traffic_data

@app.post("/traffic")
def create_traffic_observation(observation: TrafficObservation):
    record = observation.model_dump()
    record["id"] = len(traffic_data) + 1
    record["timestamp"] = datetime.now(timezone.utc)

    traffic_data.append(record)

    return {
        "message": "Traffic observation received",
        "data": record
    }

@app.get("/congestion")
def congestion():
    if not traffic_data:
        return {
            "status": "no_data",
            "message": "No traffic observations available yet"
        }

    return {
        "status": "available",
        "observations": len(traffic_data),
        "latest": traffic_data[-1]
    }
