from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


CongestionLevel = Literal[
    "low",
    "medium",
    "high",
    "critical",
]

IncidentType = Literal[
    "accident",
    "breakdown",
    "roadblock",
    "flooding",
    "congestion",
    "other",
]

IncidentSeverity = Literal[
    "low",
    "medium",
    "high",
    "critical",
]

IncidentStatus = Literal[
    "reported",
    "confirmed",
    "resolved",
    "dismissed",
]

TrafficPhase = Literal[
    "red",
    "yellow",
    "green",
    "off",
    "unknown",
]

TrafficLightStatus = Literal[
    "active",
    "maintenance",
    "offline",
]


class IntersectionCreate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=150,
    )

    city: str = Field(
        default="Kinshasa",
        min_length=2,
        max_length=100,
    )

    latitude: float | None = Field(
        default=None,
        ge=-90,
        le=90,
    )

    longitude: float | None = Field(
        default=None,
        ge=-180,
        le=180,
    )


class TrafficObservationCreate(BaseModel):
    intersection_id: int = Field(gt=0)

    vehicle_count: int = Field(
        ge=0,
    )

    average_speed: float = Field(
        ge=0,
    )

    congestion_level: CongestionLevel


class IncidentCreate(BaseModel):
    intersection_id: int = Field(gt=0)

    type: IncidentType

    severity: IncidentSeverity

    description: str | None = Field(
        default=None,
        max_length=500,
    )


class IncidentStatusUpdate(BaseModel):
    status: IncidentStatus


class TrafficLightCreate(BaseModel):
    intersection_id: int = Field(gt=0)

    current_phase: TrafficPhase = "unknown"

    green_duration: int = Field(
        default=30,
        ge=1,
        le=300,
    )

    yellow_duration: int = Field(
        default=3,
        ge=1,
        le=30,
    )

    red_duration: int = Field(
        default=30,
        ge=1,
        le=300,
    )

    status: TrafficLightStatus = "active"


class TrafficLightUpdate(BaseModel):
    current_phase: TrafficPhase | None = None

    green_duration: int | None = Field(
        default=None,
        ge=1,
        le=300,
    )

    yellow_duration: int | None = Field(
        default=None,
        ge=1,
        le=30,
    )

    red_duration: int | None = Field(
        default=None,
        ge=1,
        le=300,
    )

    status: TrafficLightStatus | None = None


EdgeSourceKind = Literal[
    "video",
    "camera",
    "rtsp",
]


class EdgeLaneMetrics(BaseModel):
    approach: str = Field(
        min_length=1,
        max_length=80,
    )

    vehicle_count: int = Field(ge=0)
    person_count: int = Field(ge=0)
    queue_count: int = Field(ge=0)

    weighted_units: float = Field(ge=0)

    density: float = Field(
        ge=0,
        le=1,
    )

    demand_score: float = Field(
        ge=0,
        le=1,
    )

    passed_total: int = Field(ge=0)
    flow_last_60s: int = Field(ge=0)
    max_queue_count: int = Field(ge=0)

    mean_stationary_s: float = Field(ge=0)


class EdgeSignalSnapshot(BaseModel):
    state: str = Field(
        min_length=1,
        max_length=80,
    )

    active_group: str | None = Field(
        default=None,
        max_length=30,
    )

    colors: dict[str, str]

    remaining_s: float = Field(ge=0)

    mode: str = Field(
        min_length=1,
        max_length=40,
    )

    target_green_s: float | None = Field(
        default=None,
        ge=0,
    )

    source: str = Field(
        min_length=1,
        max_length=40,
    )


class EdgeTelemetryCreate(BaseModel):
    schema_version: Literal["1.0"]

    edge_id: str = Field(
        min_length=3,
        max_length=80,
    )

    intersection_id: int = Field(gt=0)

    site_name: str = Field(
        min_length=2,
        max_length=150,
    )

    session_id: str = Field(
        min_length=3,
        max_length=150,
    )

    source_kind: EdgeSourceKind

    data_origin: Literal[
        "observed",
        "synthetic_test",
    ]

    processed_at: datetime

    video_time_s: float = Field(ge=0)

    data_valid: bool

    status: str = Field(
        min_length=1,
        max_length=40,
    )

    signal: EdgeSignalSnapshot

    approaches: dict[str, EdgeLaneMetrics]

    processing_ms: float = Field(ge=0)

    model_name: str = Field(
        min_length=1,
        max_length=120,
    )

    calibration_resolution: tuple[int, int] | None = None
