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