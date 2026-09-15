from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from hyperspace.services.multi_tenant_service import (
    MultiTenantService,
)


router = APIRouter(
    prefix="/api/v1",
    tags=["multi-tenant"],
)


tenant_service = MultiTenantService()


# =========================================================
# REQUEST MODELS
# =========================================================

class TenantCreateRequest(BaseModel):

    name: str = Field(
        min_length=1
    )

    quota_cpu_seconds: int = Field(
        default=3600,
        ge=0,
    )

    quota_gpu_seconds: int = Field(
        default=3600,
        ge=0,
    )

    quota_jobs: int = Field(
        default=100,
        ge=0,
    )


class ProjectCreateRequest(BaseModel):

    tenant_id: str
    name: str = Field(
        min_length=1
    )


class APIKeyCreateRequest(BaseModel):

    tenant_id: str
    project_id: str


class UsageRequest(BaseModel):

    tenant_id: str
    project_id: str

    cpu_seconds: int = Field(
        default=0,
        ge=0,
    )

    gpu_seconds: int = Field(
        default=0,
        ge=0,
    )

    jobs: int = Field(
        default=0,
        ge=0,
    )


# =========================================================
# TENANT API
# =========================================================

@router.post("/tenants")
def create_tenant(
    request: TenantCreateRequest,
):

    tenant = tenant_service.create_tenant(
        name=request.name,
        quota_cpu_seconds=(
            request.quota_cpu_seconds
        ),
        quota_gpu_seconds=(
            request.quota_gpu_seconds
        ),
        quota_jobs=request.quota_jobs,
    )

    return {
        "tenant": tenant,
    }


@router.get("/tenants")
def list_tenants():

    return {
        "tenants": tenant_service.list_tenants(),
    }


@router.get("/tenants/{tenant_id}")
def get_tenant(
    tenant_id: str,
):

    tenant = tenant_service.get_tenant(
        tenant_id
    )

    if tenant is None:

        raise HTTPException(
            status_code=404,
            detail="Tenant not found.",
        )

    return {
        "tenant": tenant,
    }


# =========================================================
# PROJECT API
# =========================================================

@router.post("/projects")
def create_project(
    request: ProjectCreateRequest,
):

    try:

        project = (
            tenant_service.create_project(
                tenant_id=request.tenant_id,
                name=request.name,
            )
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    return {
        "project": project,
    }


@router.get(
    "/tenants/{tenant_id}/projects"
)
def list_projects(
    tenant_id: str,
):

    if tenant_service.get_tenant(
        tenant_id
    ) is None:

        raise HTTPException(
            status_code=404,
            detail="Tenant not found.",
        )

    return {
        "projects": tenant_service.list_projects(
            tenant_id
        ),
    }


# =========================================================
# API KEY API
# =========================================================

@router.post("/api-keys")
def create_api_key(
    request: APIKeyCreateRequest,
):

    try:

        key, raw_key = (
            tenant_service.create_api_key(
                tenant_id=request.tenant_id,
                project_id=request.project_id,
            )
        )

    except (
        ValueError,
        PermissionError,
    ) as exc:

        raise HTTPException(
            status_code=403,
            detail=str(exc),
        )

    return {
        "key_id": key.key_id,
        "key_prefix": key.key_prefix,
        "project_id": key.project_id,
        "tenant_id": key.tenant_id,

        # The secret is returned only once.
        "api_key": raw_key,
    }


@router.post(
    "/api-keys/{key_id}/revoke"
)
def revoke_api_key(
    key_id: str,
    tenant_id: str,
):

    try:

        revoked = (
            tenant_service.revoke_api_key(
                tenant_id=tenant_id,
                key_id=key_id,
            )
        )

    except PermissionError as exc:

        raise HTTPException(
            status_code=403,
            detail=str(exc),
        )

    if not revoked:

        raise HTTPException(
            status_code=404,
            detail="API key not found.",
        )

    return {
        "revoked": True,
        "key_id": key_id,
    }


@router.get("/api-keys/validate")
def validate_api_key(
    x_api_key: str | None = Header(
        default=None
    ),
):

    result = (
        tenant_service.validate_api_key(
            x_api_key or ""
        )
    )

    if not result.valid:

        raise HTTPException(
            status_code=401,
            detail=result.error,
        )

    return {
        "valid": True,
        "tenant_id": result.tenant_id,
        "project_id": result.project_id,
        "key_id": result.key_id,
    }


# =========================================================
# USAGE API
# =========================================================

@router.get(
    "/tenants/{tenant_id}/projects/{project_id}/usage"
)
def get_usage(
    tenant_id: str,
    project_id: str,
):

    try:

        usage = (
            tenant_service.get_usage(
                tenant_id=tenant_id,
                project_id=project_id,
            )
        )

    except PermissionError as exc:

        raise HTTPException(
            status_code=403,
            detail=str(exc),
        )

    return {
        "usage": usage,
    }


@router.post("/usage")
def record_usage(
    request: UsageRequest,
):

    try:

        usage = (
            tenant_service.record_usage(
                tenant_id=request.tenant_id,
                project_id=request.project_id,
                cpu_seconds=request.cpu_seconds,
                gpu_seconds=request.gpu_seconds,
                jobs=request.jobs,
            )
        )

    except PermissionError as exc:

        raise HTTPException(
            status_code=403,
            detail=str(exc),
        )

    except RuntimeError as exc:

        raise HTTPException(
            status_code=429,
            detail=str(exc),
        )

    return {
        "usage": usage,
    }