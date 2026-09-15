from __future__ import annotations

import time
import uuid
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


# =========================================================
# APPLICATION
# =========================================================

app = FastAPI(
    title="Hyperspace Public Compute API",
    version="1.0.0",
    description=(
        "Public API foundation for the Hyperspace "
        "distributed compute mesh."
    ),
)


# =========================================================
# IN-MEMORY API STATE
#
# M24 is establishing the public API contract.
# Persistent database/storage comes during production
# hardening.
# =========================================================

NODES: dict[str, dict[str, Any]] = {}
JOBS: dict[str, dict[str, Any]] = {}
RESULTS: dict[str, dict[str, Any]] = {}


# =========================================================
# MODELS
# =========================================================

class NodeRegistration(BaseModel):

    node_id: str = Field(
        min_length=1
    )

    hostname: str = Field(
        min_length=1
    )

    cpu_cores: int = Field(
        ge=1
    )

    ram_mb: int = Field(
        ge=1
    )

    gpu_count: int = Field(
        ge=0
    )


class JobSubmission(BaseModel):

    job_type: str = Field(
        min_length=1
    )

    payload: dict[str, Any] = Field(
        default_factory=dict
    )

    requirements: dict[str, Any] = Field(
        default_factory=dict
    )


class JobResponse(BaseModel):

    job_id: str
    status: str
    job_type: str


# =========================================================
# HEALTH
# =========================================================

@app.get("/")
def root() -> dict[str, Any]:

    return {
        "service": "Hyperspace Public Compute API",
        "version": "1.0.0",
        "status": "online",
    }


@app.get("/health")
def health() -> dict[str, Any]:

    return {
        "status": "healthy",
        "service": "hyperspace-public-api",
        "timestamp": time.time(),
    }


# =========================================================
# M24.3 NODE API
# =========================================================

@app.get("/api/v1/nodes")
def list_nodes() -> dict[str, Any]:

    return {
        "nodes": list(
            NODES.values()
        ),
        "count": len(NODES),
    }


@app.post("/api/v1/nodes")
def register_node(
    node: NodeRegistration,
) -> dict[str, Any]:

    if node.node_id in NODES:

        raise HTTPException(
            status_code=409,
            detail="Node already registered.",
        )

    record = {
        "node_id": node.node_id,
        "hostname": node.hostname,
        "cpu_cores": node.cpu_cores,
        "ram_mb": node.ram_mb,
        "gpu_count": node.gpu_count,
        "status": "available",
        "registered_at": time.time(),
    }

    NODES[node.node_id] = record

    return {
        "accepted": True,
        "node": record,
    }


@app.get("/api/v1/nodes/{node_id}")
def get_node(
    node_id: str,
) -> dict[str, Any]:

    node = NODES.get(
        node_id
    )

    if node is None:

        raise HTTPException(
            status_code=404,
            detail="Node not found.",
        )

    return node


@app.delete("/api/v1/nodes/{node_id}")
def remove_node(
    node_id: str,
) -> dict[str, Any]:

    if node_id not in NODES:

        raise HTTPException(
            status_code=404,
            detail="Node not found.",
        )

    del NODES[node_id]

    return {
        "removed": True,
        "node_id": node_id,
    }


# =========================================================
# M24.3 RESOURCE API
# =========================================================

@app.get("/api/v1/resources")
def resources() -> dict[str, Any]:

    total_cpu = sum(
        node["cpu_cores"]
        for node in NODES.values()
    )

    total_ram = sum(
        node["ram_mb"]
        for node in NODES.values()
    )

    total_gpu = sum(
        node["gpu_count"]
        for node in NODES.values()
    )

    return {
        "nodes": len(NODES),
        "cpu_cores": total_cpu,
        "ram_mb": total_ram,
        "gpu_count": total_gpu,
    }


# =========================================================
# M24.4 JOB API
# =========================================================

@app.post(
    "/api/v1/jobs",
    response_model=JobResponse,
)
def submit_job(
    submission: JobSubmission,
) -> JobResponse:

    job_id = str(
        uuid.uuid4()
    )

    job = {
        "job_id": job_id,
        "job_type": submission.job_type,
        "payload": submission.payload,
        "requirements": submission.requirements,
        "status": "queued",
        "submitted_at": time.time(),
    }

    JOBS[job_id] = job

    return JobResponse(
        job_id=job_id,
        status="queued",
        job_type=submission.job_type,
    )


@app.get("/api/v1/jobs")
def list_jobs() -> dict[str, Any]:

    return {
        "jobs": list(
            JOBS.values()
        ),
        "count": len(JOBS),
    }


@app.get("/api/v1/jobs/{job_id}")
def get_job(
    job_id: str,
) -> dict[str, Any]:

    job = JOBS.get(
        job_id
    )

    if job is None:

        raise HTTPException(
            status_code=404,
            detail="Job not found.",
        )

    return job


@app.delete("/api/v1/jobs/{job_id}")
def cancel_job(
    job_id: str,
) -> dict[str, Any]:

    job = JOBS.get(
        job_id
    )

    if job is None:

        raise HTTPException(
            status_code=404,
            detail="Job not found.",
        )

    if job["status"] in {
        "completed",
        "failed",
    }:

        raise HTTPException(
            status_code=409,
            detail="Job can no longer be cancelled.",
        )

    job["status"] = "cancelled"

    return {
        "cancelled": True,
        "job_id": job_id,
    }


# =========================================================
# M24.4 RESULT API
# =========================================================

@app.get("/api/v1/jobs/{job_id}/result")
def get_result(
    job_id: str,
) -> dict[str, Any]:

    if job_id not in JOBS:

        raise HTTPException(
            status_code=404,
            detail="Job not found.",
        )

    result = RESULTS.get(
        job_id
    )

    if result is None:

        return {
            "job_id": job_id,
            "available": False,
            "result": None,
        }

    return {
        "job_id": job_id,
        "available": True,
        "result": result,
    }


# =========================================================
# API SUMMARY
# =========================================================

@app.get("/api/v1")
def api_information() -> dict[str, Any]:

    return {
        "name": "Hyperspace Public Compute API",
        "version": "1.0.0",
        "endpoints": {
            "nodes": [
                "GET /api/v1/nodes",
                "POST /api/v1/nodes",
                "GET /api/v1/nodes/{node_id}",
                "DELETE /api/v1/nodes/{node_id}",
            ],
            "resources": [
                "GET /api/v1/resources",
            ],
            "jobs": [
                "GET /api/v1/jobs",
                "POST /api/v1/jobs",
                "GET /api/v1/jobs/{job_id}",
                "DELETE /api/v1/jobs/{job_id}",
            ],
            "results": [
                "GET /api/v1/jobs/{job_id}/result",
            ],
        },
    }


from apps.public_api.tenant_api import router as tenant_router

app.include_router(
    tenant_router
)