from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.database import (
    Base,
    SessionLocal,
    engine,
    get_db,
)

from app.models import (
    Incident,
    Intersection,
    OSMFeature,
    TrafficLight,
    TrafficObservation,
)

from app.schemas import (
    IncidentCreate,
    IncidentStatusUpdate,
    IntersectionCreate,
    TrafficLightCreate,
    TrafficLightUpdate,
    TrafficObservationCreate,
)

from app.security import verify_admin_key, verify_ingest_key


BASE_DIR = Path(__file__).resolve().parent.parent
DASHBOARD_DIR = BASE_DIR / "dashboard"


def intersection_to_dict(row):
    return {
        "id": row.id,
        "name": row.name,
        "city": row.city,
        "latitude": row.latitude,
        "longitude": row.longitude,
    }


def observation_to_dict(row):
    return {
        "id": row.id,
        "intersection_id": row.intersection_id,
        "vehicle_count": row.vehicle_count,
        "average_speed": row.average_speed,
        "congestion_level": row.congestion_level,
        "timestamp": row.timestamp,
    }


def incident_to_dict(row):
    return {
        "id": row.id,
        "intersection_id": row.intersection_id,
        "type": row.incident_type,
        "severity": row.severity,
        "description": row.description,
        "status": row.status,
        "reported_at": row.reported_at,
        "resolved_at": row.resolved_at,
    }


def traffic_light_to_dict(row):
    return {
        "id": row.id,
        "intersection_id": row.intersection_id,
        "current_phase": row.current_phase,
        "green_duration": row.green_duration,
        "yellow_duration": row.yellow_duration,
        "red_duration": row.red_duration,
        "status": row.status,
        "updated_at": row.updated_at,
    }


def osm_feature_to_dict(row):
    return {
        "id": row.id,
        "osm_type": row.osm_type,
        "osm_id": row.osm_id,
        "feature_type": row.feature_type,
        "name": row.name,
        "latitude": row.latitude,
        "longitude": row.longitude,
    }


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        if db.query(Intersection).count() == 0:
            db.add_all(
                [
                    Intersection(
                        name="Rond-point Victoire",
                        city="Kinshasa",
                    ),
                    Intersection(
                        name="Rond-point Ngaba",
                        city="Kinshasa",
                    ),
                ]
            )

            db.commit()

    finally:
        db.close()

    yield


app = FastAPI(
    title="KinTraffic API",
    description=(
        "Urban mobility and intelligent traffic "
        "management platform for Kinshasa"
    ),
    version="0.6.0",
    lifespan=lifespan,
)



app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=[
        "kintraffic-api-347eebddca06.herokuapp.com",
        "*.herokuapp.com",
        "localhost",
        "127.0.0.1",
    ],
)


@app.middleware("http")
async def security_headers(
    request: Request,
    call_next,
):
    response = await call_next(request)

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = (
        "camera=(), microphone=(), geolocation=(), payment=()"
    )
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' https://unpkg.com; "
        "style-src 'self' 'unsafe-inline' https://unpkg.com; "
        "img-src 'self' data: https://*.tile.openstreetmap.org; "
        "connect-src 'self'; "
        "font-src 'self' data:; "
        "object-src 'none'; "
        "frame-src 'none'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self';"
    )

    return response


app.mount(
    "/dashboard",
    StaticFiles(
        directory=str(DASHBOARD_DIR),
        html=True,
    ),
    name="dashboard",
)


@app.get("/")
def home():
    return {
        "project": "KinTraffic",
        "version": "0.6.0",
        "status": "online",
        "city": "Kinshasa",
        "database": "PostgreSQL",
        "dashboard": "/dashboard/",
        "documentation": "/docs",
        "features": [
            "traffic",
            "intersections",
            "incidents",
            "traffic lights",
            "analytics",
            "OpenStreetMap geographic data",
            "control center dashboard",
        ],
    }


@app.get("/health")
def health(
    db: Session = Depends(get_db),
):
    db.execute(text("SELECT 1"))

    return {
        "status": "healthy",
        "database": "connected",
        "version": "0.6.0",
    }


@app.get("/intersections")
def get_intersections(
    db: Session = Depends(get_db),
):
    rows = (
        db.query(Intersection)
        .order_by(Intersection.id)
        .all()
    )

    return [
        intersection_to_dict(row)
        for row in rows
    ]


@app.get("/intersections/{intersection_id}")
def get_intersection(
    intersection_id: int,
    db: Session = Depends(get_db),
):
    row = (
        db.query(Intersection)
        .filter(
            Intersection.id == intersection_id
        )
        .first()
    )

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Intersection not found",
        )

    return intersection_to_dict(row)


@app.post(
    "/intersections",
    status_code=201,
)
def create_intersection(
    payload: IntersectionCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_admin_key),
):
    row = Intersection(
        name=payload.name,
        city=payload.city,
        latitude=payload.latitude,
        longitude=payload.longitude,
    )

    db.add(row)
    db.commit()
    db.refresh(row)

    return {
        "message": "Intersection created",
        "data": intersection_to_dict(row),
    }


@app.get("/traffic")
def get_traffic(
    db: Session = Depends(get_db),
):
    rows = (
        db.query(TrafficObservation)
        .order_by(
            TrafficObservation.timestamp.desc()
        )
        .limit(100)
        .all()
    )

    return [
        observation_to_dict(row)
        for row in rows
    ]


@app.post(
    "/traffic",
    status_code=201,
)
def create_traffic_observation(
    payload: TrafficObservationCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_ingest_key),
):
    intersection = (
        db.query(Intersection)
        .filter(
            Intersection.id
            == payload.intersection_id
        )
        .first()
    )

    if intersection is None:
        raise HTTPException(
            status_code=404,
            detail="Intersection not found",
        )

    row = TrafficObservation(
        intersection_id=payload.intersection_id,
        vehicle_count=payload.vehicle_count,
        average_speed=payload.average_speed,
        congestion_level=payload.congestion_level,
    )

    db.add(row)
    db.commit()
    db.refresh(row)

    return {
        "message": (
            "Traffic observation stored permanently"
        ),
        "data": observation_to_dict(row),
    }


@app.get("/congestion")
def congestion(
    db: Session = Depends(get_db),
):
    total = (
        db.query(
            func.count(
                TrafficObservation.id
            )
        )
        .scalar()
        or 0
    )

    latest = (
        db.query(TrafficObservation)
        .order_by(
            TrafficObservation.timestamp.desc()
        )
        .first()
    )

    return {
        "status": (
            "available"
            if latest
            else "no_data"
        ),
        "observations": total,
        "latest": (
            observation_to_dict(latest)
            if latest
            else None
        ),
    }


@app.get("/incidents")
def get_incidents(
    db: Session = Depends(get_db),
):
    rows = (
        db.query(Incident)
        .order_by(
            Incident.reported_at.desc()
        )
        .limit(100)
        .all()
    )

    return [
        incident_to_dict(row)
        for row in rows
    ]


@app.post(
    "/incidents",
    status_code=201,
)
def create_incident(
    payload: IncidentCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_ingest_key),
):
    intersection = (
        db.query(Intersection)
        .filter(
            Intersection.id
            == payload.intersection_id
        )
        .first()
    )

    if intersection is None:
        raise HTTPException(
            status_code=404,
            detail="Intersection not found",
        )

    row = Incident(
        intersection_id=payload.intersection_id,
        incident_type=payload.type,
        severity=payload.severity,
        description=payload.description,
        status="reported",
    )

    db.add(row)
    db.commit()
    db.refresh(row)

    return {
        "message": "Incident reported",
        "data": incident_to_dict(row),
    }


@app.patch(
    "/incidents/{incident_id}/status"
)
def update_incident_status(
    incident_id: int,
    payload: IncidentStatusUpdate,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_admin_key),
):
    row = (
        db.query(Incident)
        .filter(
            Incident.id == incident_id
        )
        .first()
    )

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Incident not found",
        )

    row.status = payload.status

    if payload.status == "resolved":
        row.resolved_at = datetime.now(
            timezone.utc
        )

    elif row.resolved_at is not None:
        row.resolved_at = None

    db.commit()
    db.refresh(row)

    return {
        "message": "Incident status updated",
        "data": incident_to_dict(row),
    }


@app.get("/traffic-lights")
def get_traffic_lights(
    db: Session = Depends(get_db),
):
    rows = (
        db.query(TrafficLight)
        .order_by(TrafficLight.id)
        .all()
    )

    return [
        traffic_light_to_dict(row)
        for row in rows
    ]


@app.post(
    "/traffic-lights",
    status_code=201,
)
def create_traffic_light(
    payload: TrafficLightCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_admin_key),
):
    intersection = (
        db.query(Intersection)
        .filter(
            Intersection.id
            == payload.intersection_id
        )
        .first()
    )

    if intersection is None:
        raise HTTPException(
            status_code=404,
            detail="Intersection not found",
        )

    existing = (
        db.query(TrafficLight)
        .filter(
            TrafficLight.intersection_id
            == payload.intersection_id
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail=(
                "A traffic light already exists "
                "for this intersection"
            ),
        )

    row = TrafficLight(
        intersection_id=payload.intersection_id,
        current_phase=payload.current_phase,
        green_duration=payload.green_duration,
        yellow_duration=payload.yellow_duration,
        red_duration=payload.red_duration,
        status=payload.status,
    )

    db.add(row)
    db.commit()
    db.refresh(row)

    return {
        "message": "Traffic light created",
        "data": traffic_light_to_dict(row),
    }


@app.patch(
    "/traffic-lights/{traffic_light_id}"
)
def update_traffic_light(
    traffic_light_id: int,
    payload: TrafficLightUpdate,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_admin_key),
):
    row = (
        db.query(TrafficLight)
        .filter(
            TrafficLight.id
            == traffic_light_id
        )
        .first()
    )

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Traffic light not found",
        )

    changes = payload.model_dump(
        exclude_unset=True,
        exclude_none=True,
    )

    if not changes:
        raise HTTPException(
            status_code=400,
            detail="No changes supplied",
        )

    for key, value in changes.items():
        setattr(row, key, value)

    db.commit()
    db.refresh(row)

    return {
        "message": "Traffic light updated",
        "data": traffic_light_to_dict(row),
    }


@app.get("/map/features")
def get_map_features(
    feature_type: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(OSMFeature)

    if feature_type:
        query = query.filter(
            OSMFeature.feature_type
            == feature_type
        )

    rows = (
        query
        .order_by(OSMFeature.id)
        .all()
    )

    features = [
        osm_feature_to_dict(row)
        for row in rows
    ]

    return {
        "source": "OpenStreetMap",
        "attribution": (
            "© OpenStreetMap contributors"
        ),
        "count": len(features),
        "features": features,
    }


@app.get("/analytics/summary")
def analytics_summary(
    db: Session = Depends(get_db),
):
    intersections = (
        db.query(
            func.count(Intersection.id)
        )
        .scalar()
        or 0
    )

    observations = (
        db.query(
            func.count(TrafficObservation.id)
        )
        .scalar()
        or 0
    )

    incidents = (
        db.query(
            func.count(Incident.id)
        )
        .scalar()
        or 0
    )

    active_incidents = (
        db.query(
            func.count(Incident.id)
        )
        .filter(
            Incident.status.in_(
                [
                    "reported",
                    "confirmed",
                ]
            )
        )
        .scalar()
        or 0
    )

    traffic_lights = (
        db.query(
            func.count(TrafficLight.id)
        )
        .scalar()
        or 0
    )

    osm_features = (
        db.query(
            func.count(OSMFeature.id)
        )
        .scalar()
        or 0
    )

    traffic_signals = (
        db.query(
            func.count(OSMFeature.id)
        )
        .filter(
            OSMFeature.feature_type
            == "traffic_signal"
        )
        .scalar()
        or 0
    )

    roundabouts = (
        db.query(
            func.count(OSMFeature.id)
        )
        .filter(
            OSMFeature.feature_type
            == "roundabout"
        )
        .scalar()
        or 0
    )

    average_speed = (
        db.query(
            func.avg(
                TrafficObservation.average_speed
            )
        )
        .scalar()
    )

    return {
        "intersections": intersections,
        "traffic_observations": observations,
        "incidents": incidents,
        "active_incidents": active_incidents,
        "traffic_lights": traffic_lights,
        "osm_features": osm_features,
        "traffic_signals": traffic_signals,
        "roundabouts": roundabouts,
        "average_speed": (
            round(
                float(average_speed),
                2,
            )
            if average_speed is not None
            else None
        ),
    }