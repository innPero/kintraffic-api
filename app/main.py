from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.database import Base, SessionLocal, engine, get_db
from app.models import Intersection, TrafficObservation


class TrafficObservationCreate(BaseModel):
    intersection_id: int
    vehicle_count: int = Field(ge=0)
    average_speed: float = Field(ge=0)
    congestion_level: str


def observation_to_dict(record):
    return {
        "id": record.id,
        "intersection_id": record.intersection_id,
        "vehicle_count": record.vehicle_count,
        "average_speed": record.average_speed,
        "congestion_level": record.congestion_level,
        "timestamp": record.timestamp,
    }


@asynccontextmanager
async def lifespan(app: FastAPI):

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        if db.query(Intersection).count() == 0:

            db.add_all([
                Intersection(
                    name="Rond-point Victoire",
                    city="Kinshasa"
                ),
                Intersection(
                    name="Rond-point Ngaba",
                    city="Kinshasa"
                )
            ])

            db.commit()

    finally:
        db.close()

    yield


app = FastAPI(
    title="KinTraffic API",
    description="Intelligent traffic management platform for Kinshasa",
    version="0.2.0",
    lifespan=lifespan,
)


@app.get("/")
def home():
    return {
        "project": "KinTraffic",
        "version": "0.2.0",
        "status": "online",
        "city": "Kinshasa",
        "database": "PostgreSQL",
        "message": "KinTraffic API is running"
    }


@app.get("/health")
def health(db: Session = Depends(get_db)):

    db.execute(text("SELECT 1"))

    return {
        "status": "healthy",
        "database": "connected"
    }


@app.get("/intersections")
def get_intersections(db: Session = Depends(get_db)):

    rows = db.query(Intersection).order_by(Intersection.id).all()

    return [
        {
            "id": row.id,
            "name": row.name,
            "city": row.city,
            "latitude": row.latitude,
            "longitude": row.longitude
        }
        for row in rows
    ]


@app.get("/traffic")
def get_traffic(db: Session = Depends(get_db)):

    rows = (
        db.query(TrafficObservation)
        .order_by(TrafficObservation.timestamp.desc())
        .limit(100)
        .all()
    )

    return [observation_to_dict(row) for row in rows]


@app.post("/traffic")
def create_traffic_observation(
    observation: TrafficObservationCreate,
    db: Session = Depends(get_db)
):

    intersection = (
        db.query(Intersection)
        .filter(Intersection.id == observation.intersection_id)
        .first()
    )

    if intersection is None:
        raise HTTPException(
            status_code=404,
            detail="Intersection not found"
        )

    record = TrafficObservation(
        intersection_id=observation.intersection_id,
        vehicle_count=observation.vehicle_count,
        average_speed=observation.average_speed,
        congestion_level=observation.congestion_level
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "message": "Traffic observation stored permanently",
        "data": observation_to_dict(record)
    }


@app.get("/congestion")
def congestion(db: Session = Depends(get_db)):

    total = db.query(func.count(TrafficObservation.id)).scalar()

    latest = (
        db.query(TrafficObservation)
        .order_by(TrafficObservation.timestamp.desc())
        .first()
    )

    if latest is None:
        return {
            "status": "no_data",
            "observations": 0
        }

    return {
        "status": "available",
        "observations": total,
        "latest": observation_to_dict(latest)
    }
