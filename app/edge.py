from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    EdgeNode,
    EdgeSnapshot,
    Intersection,
)
from app.schemas import EdgeTelemetryCreate
from app.security import verify_ingest_key


router = APIRouter(
    prefix="/edge",
    tags=["edge"],
)


def node_to_dict(row: EdgeNode) -> dict:
    return {
        "id": row.id,
        "edge_id": row.edge_id,
        "intersection_id": row.intersection_id,
        "site_name": row.site_name,
        "schema_version": row.schema_version,
        "source_kind": row.source_kind,
        "model_name": row.model_name,
        "last_session_id": row.last_session_id,
        "status": row.status,
        "last_data_valid": row.last_data_valid,
        "created_at": row.created_at,
        "last_seen": row.last_seen,
    }


def snapshot_to_dict(row: EdgeSnapshot) -> dict:
    return {
        "id": row.id,
        "edge_node_id": row.edge_node_id,
        "intersection_id": row.intersection_id,
        "session_id": row.session_id,
        "source_kind": row.source_kind,
        "data_origin": row.data_origin,
        "processed_at": row.processed_at,
        "received_at": row.received_at,
        "video_time_s": row.video_time_s,
        "data_valid": row.data_valid,
        "status": row.status,
        "processing_ms": row.processing_ms,
        "signal": row.signal,
        "approaches": row.approaches,
        "model_name": row.model_name,
        "calibration_resolution": row.calibration_resolution,
    }


@router.post(
    "/telemetry",
    status_code=201,
)
def ingest_edge_telemetry(
    payload: EdgeTelemetryCreate,
    response: Response,
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

    for name, lane in payload.approaches.items():
        if lane.approach != name:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Approach key '{name}' does not "
                    "match lane.approach"
                ),
            )

    sample_key = (
        f"{payload.edge_id}|"
        f"{payload.session_id}|"
        f"{payload.video_time_s:.3f}"
    )

    existing_snapshot = (
        db.query(EdgeSnapshot)
        .filter(
            EdgeSnapshot.sample_key
            == sample_key
        )
        .first()
    )

    if existing_snapshot is not None:
        response.status_code = 200

        return {
            "message": "Edge telemetry already stored",
            "duplicate": True,
            "data": snapshot_to_dict(
                existing_snapshot
            ),
        }

    node = (
        db.query(EdgeNode)
        .filter(
            EdgeNode.edge_id
            == payload.edge_id
        )
        .first()
    )

    if (
        node is not None
        and node.intersection_id
        != payload.intersection_id
    ):
        raise HTTPException(
            status_code=409,
            detail=(
                "Edge node is already assigned "
                "to another intersection"
            ),
        )

    now = datetime.now(timezone.utc)

    if node is None:
        node = EdgeNode(
            edge_id=payload.edge_id,
            intersection_id=payload.intersection_id,
            site_name=payload.site_name,
            schema_version=payload.schema_version,
        )

        db.add(node)
        db.flush()

    node.site_name = payload.site_name
    node.schema_version = payload.schema_version
    node.source_kind = payload.source_kind
    node.model_name = payload.model_name
    node.last_session_id = payload.session_id
    node.status = payload.status
    node.last_data_valid = payload.data_valid
    node.last_seen = now

    snapshot = EdgeSnapshot(
        edge_node_id=node.id,
        intersection_id=payload.intersection_id,
        sample_key=sample_key,
        session_id=payload.session_id,
        source_kind=payload.source_kind,
        data_origin=payload.data_origin,
        processed_at=payload.processed_at,
        video_time_s=payload.video_time_s,
        data_valid=payload.data_valid,
        status=payload.status,
        processing_ms=payload.processing_ms,
        signal=payload.signal.model_dump(),
        approaches={
            name: lane.model_dump()
            for name, lane
            in payload.approaches.items()
        },
        model_name=payload.model_name,
        calibration_resolution=(
            list(payload.calibration_resolution)
            if payload.calibration_resolution
            else None
        ),
    )

    db.add(snapshot)
    db.commit()

    db.refresh(node)
    db.refresh(snapshot)

    return {
        "message": "Edge telemetry stored",
        "duplicate": False,
        "edge": node_to_dict(node),
        "data": snapshot_to_dict(snapshot),
    }


@router.get("/nodes")
def get_edge_nodes(
    db: Session = Depends(get_db),
):
    rows = (
        db.query(EdgeNode)
        .order_by(EdgeNode.edge_id)
        .all()
    )

    return [
        node_to_dict(row)
        for row in rows
    ]


@router.get("/nodes/{edge_id}")
def get_edge_node(
    edge_id: str,
    db: Session = Depends(get_db),
):
    node = (
        db.query(EdgeNode)
        .filter(
            EdgeNode.edge_id == edge_id
        )
        .first()
    )

    if node is None:
        raise HTTPException(
            status_code=404,
            detail="Edge node not found",
        )

    latest = (
        db.query(EdgeSnapshot)
        .filter(
            EdgeSnapshot.edge_node_id
            == node.id
        )
        .order_by(
            EdgeSnapshot.received_at.desc()
        )
        .first()
    )

    return {
        "edge": node_to_dict(node),
        "latest": (
            snapshot_to_dict(latest)
            if latest
            else None
        ),
    }


@router.get(
    "/intersections/{intersection_id}/latest"
)
def get_latest_edge_snapshot(
    intersection_id: int,
    db: Session = Depends(get_db),
):
    latest = (
        db.query(EdgeSnapshot)
        .filter(
            EdgeSnapshot.intersection_id
            == intersection_id
        )
        .order_by(
            EdgeSnapshot.received_at.desc()
        )
        .first()
    )

    if latest is None:
        raise HTTPException(
            status_code=404,
            detail="No Edge telemetry available",
        )

    return snapshot_to_dict(latest)
