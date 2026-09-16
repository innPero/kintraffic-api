from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    func,
)

from app.database import Base


class Intersection(Base):
    __tablename__ = "intersections"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    city = Column(String(100), default="Kinshasa")
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)


class TrafficObservation(Base):
    __tablename__ = "traffic_observations"

    id = Column(Integer, primary_key=True, index=True)

    intersection_id = Column(
        Integer,
        ForeignKey("intersections.id"),
        nullable=False,
        index=True,
    )

    vehicle_count = Column(Integer, nullable=False)
    average_speed = Column(Float, nullable=False)
    congestion_level = Column(String(30), nullable=False)

    timestamp = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class TrafficLight(Base):
    __tablename__ = "traffic_lights"

    id = Column(Integer, primary_key=True, index=True)

    intersection_id = Column(
        Integer,
        ForeignKey("intersections.id"),
        nullable=False,
        unique=True,
        index=True,
    )

    current_phase = Column(
        String(20),
        default="unknown",
        nullable=False,
    )

    green_duration = Column(
        Integer,
        default=30,
        nullable=False,
    )

    yellow_duration = Column(
        Integer,
        default=3,
        nullable=False,
    )

    red_duration = Column(
        Integer,
        default=30,
        nullable=False,
    )

    status = Column(
        String(30),
        default="active",
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)

    intersection_id = Column(
        Integer,
        ForeignKey("intersections.id"),
        nullable=False,
        index=True,
    )

    incident_type = Column(
        "type",
        String(50),
        nullable=False,
    )

    severity = Column(
        String(20),
        nullable=False,
    )

    description = Column(
        Text,
        nullable=True,
    )

    status = Column(
        String(30),
        default="reported",
        nullable=False,
    )

    reported_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    resolved_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )


class OSMFeature(Base):
    __tablename__ = "osm_features"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    osm_key = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    osm_type = Column(
        String(20),
        nullable=False,
    )

    osm_id = Column(
        BigInteger,
        nullable=False,
    )

    feature_type = Column(
        String(50),
        nullable=False,
        index=True,
    )

    name = Column(
        String(200),
        nullable=False,
    )

    latitude = Column(
        Float,
        nullable=False,
    )

    longitude = Column(
        Float,
        nullable=False,
    )

    tags = Column(
        JSON,
        nullable=True,
    )

    source = Column(
        String(50),
        default="OpenStreetMap",
        nullable=False,
    )

    imported_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
