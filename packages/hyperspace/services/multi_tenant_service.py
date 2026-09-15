from __future__ import annotations

import hashlib
import secrets
import time
import uuid
from dataclasses import asdict, dataclass


# =========================================================
# TENANT
# =========================================================

@dataclass
class Tenant:
    tenant_id: str
    name: str
    created_at: float
    quota_cpu_seconds: int
    quota_gpu_seconds: int
    quota_jobs: int


# =========================================================
# PROJECT
# =========================================================

@dataclass
class Project:
    project_id: str
    tenant_id: str
    name: str
    created_at: float


# =========================================================
# API KEY
# =========================================================

@dataclass
class APIKey:
    key_id: str
    tenant_id: str
    project_id: str
    key_prefix: str
    key_hash: str
    created_at: float
    revoked: bool = False


# =========================================================
# USAGE
# =========================================================

@dataclass
class UsageRecord:
    tenant_id: str
    project_id: str
    jobs: int = 0
    cpu_seconds: int = 0
    gpu_seconds: int = 0


# =========================================================
# AUTH RESULT
# =========================================================

@dataclass
class APIKeyValidation:
    valid: bool
    tenant_id: str | None = None
    project_id: str | None = None
    key_id: str | None = None
    error: str | None = None


# =========================================================
# MULTI-TENANT SERVICE
# =========================================================

class MultiTenantService:

    API_KEY_PREFIX = "hsp_"

    def __init__(self) -> None:

        self._tenants: dict[
            str,
            Tenant,
        ] = {}

        self._projects: dict[
            str,
            Project,
        ] = {}

        self._keys: dict[
            str,
            APIKey,
        ] = {}

        self._usage: dict[
            tuple[str, str],
            UsageRecord,
        ] = {}

    # =====================================================
    # TENANTS
    # =====================================================

    def create_tenant(
        self,
        name: str,
        quota_cpu_seconds: int = 3600,
        quota_gpu_seconds: int = 3600,
        quota_jobs: int = 100,
    ) -> Tenant:

        name = name.strip()

        if not name:
            raise ValueError(
                "Tenant name cannot be empty."
            )

        if quota_cpu_seconds < 0:
            raise ValueError(
                "CPU quota cannot be negative."
            )

        if quota_gpu_seconds < 0:
            raise ValueError(
                "GPU quota cannot be negative."
            )

        if quota_jobs < 0:
            raise ValueError(
                "Job quota cannot be negative."
            )

        tenant = Tenant(
            tenant_id=str(
                uuid.uuid4()
            ),
            name=name,
            created_at=time.time(),
            quota_cpu_seconds=quota_cpu_seconds,
            quota_gpu_seconds=quota_gpu_seconds,
            quota_jobs=quota_jobs,
        )

        self._tenants[
            tenant.tenant_id
        ] = tenant

        return tenant

    def get_tenant(
        self,
        tenant_id: str,
    ) -> Tenant | None:

        return self._tenants.get(
            tenant_id
        )

    def list_tenants(self) -> list[Tenant]:

        return list(
            self._tenants.values()
        )

    # =====================================================
    # PROJECTS
    # =====================================================

    def create_project(
        self,
        tenant_id: str,
        name: str,
    ) -> Project:

        tenant = self.get_tenant(
            tenant_id
        )

        if tenant is None:
            raise ValueError(
                "Tenant not found."
            )

        name = name.strip()

        if not name:
            raise ValueError(
                "Project name cannot be empty."
            )

        project = Project(
            project_id=str(
                uuid.uuid4()
            ),
            tenant_id=tenant_id,
            name=name,
            created_at=time.time(),
        )

        self._projects[
            project.project_id
        ] = project

        self._usage[
            (
                tenant_id,
                project.project_id,
            )
        ] = UsageRecord(
            tenant_id=tenant_id,
            project_id=project.project_id,
        )

        return project

    def get_project(
        self,
        project_id: str,
    ) -> Project | None:

        return self._projects.get(
            project_id
        )

    def list_projects(
        self,
        tenant_id: str,
    ) -> list[Project]:

        return [
            project
            for project in self._projects.values()
            if project.tenant_id == tenant_id
        ]

    def assert_project_access(
        self,
        tenant_id: str,
        project_id: str,
    ) -> Project:

        project = self.get_project(
            project_id
        )

        if project is None:
            raise PermissionError(
                "Project not found."
            )

        if project.tenant_id != tenant_id:
            raise PermissionError(
                "Tenant does not own this project."
            )

        return project

    # =====================================================
    # API KEYS
    # =====================================================

    @staticmethod
    def _hash_key(
        raw_key: str,
    ) -> str:

        return hashlib.sha256(
            raw_key.encode(
                "utf-8"
            )
        ).hexdigest()

    def create_api_key(
        self,
        tenant_id: str,
        project_id: str,
    ) -> tuple[APIKey, str]:

        self.assert_project_access(
            tenant_id=tenant_id,
            project_id=project_id,
        )

        key_id = str(
            uuid.uuid4()
        )

        secret = secrets.token_urlsafe(
            32
        )

        raw_key = (
            f"{self.API_KEY_PREFIX}"
            f"{key_id.replace('-', '')[:12]}_"
            f"{secret}"
        )

        key = APIKey(
            key_id=key_id,
            tenant_id=tenant_id,
            project_id=project_id,
            key_prefix=raw_key[:16],
            key_hash=self._hash_key(
                raw_key
            ),
            created_at=time.time(),
        )

        self._keys[
            key_id
        ] = key

        return key, raw_key

    def revoke_api_key(
        self,
        tenant_id: str,
        key_id: str,
    ) -> bool:

        key = self._keys.get(
            key_id
        )

        if key is None:
            return False

        if key.tenant_id != tenant_id:
            raise PermissionError(
                "Tenant does not own this API key."
            )

        key.revoked = True

        return True

    def validate_api_key(
        self,
        raw_key: str,
    ) -> APIKeyValidation:

        if not raw_key:
            return APIKeyValidation(
                valid=False,
                error="API key is required.",
            )

        key_hash = self._hash_key(
            raw_key
        )

        for key in self._keys.values():

            if key.key_hash != key_hash:
                continue

            if key.revoked:
                return APIKeyValidation(
                    valid=False,
                    error="API key has been revoked.",
                )

            return APIKeyValidation(
                valid=True,
                tenant_id=key.tenant_id,
                project_id=key.project_id,
                key_id=key.key_id,
            )

        return APIKeyValidation(
            valid=False,
            error="Invalid API key.",
        )

    # =====================================================
    # USAGE
    # =====================================================

    def get_usage(
        self,
        tenant_id: str,
        project_id: str,
    ) -> UsageRecord:

        self.assert_project_access(
            tenant_id=tenant_id,
            project_id=project_id,
        )

        return self._usage[
            (
                tenant_id,
                project_id,
            )
        ]

    def check_quota(
        self,
        tenant_id: str,
        project_id: str,
        cpu_seconds: int = 0,
        gpu_seconds: int = 0,
        jobs: int = 0,
    ) -> bool:

        project = self.assert_project_access(
            tenant_id=tenant_id,
            project_id=project_id,
        )

        tenant = self.get_tenant(
            tenant_id
        )

        if tenant is None:
            raise ValueError(
                "Tenant not found."
            )

        usage = self._usage[
            (
                tenant_id,
                project.project_id,
            )
        ]

        if (
            usage.cpu_seconds
            + cpu_seconds
            > tenant.quota_cpu_seconds
        ):
            return False

        if (
            usage.gpu_seconds
            + gpu_seconds
            > tenant.quota_gpu_seconds
        ):
            return False

        if (
            usage.jobs
            + jobs
            > tenant.quota_jobs
        ):
            return False

        return True

    def record_usage(
        self,
        tenant_id: str,
        project_id: str,
        cpu_seconds: int = 0,
        gpu_seconds: int = 0,
        jobs: int = 0,
    ) -> UsageRecord:

        self.assert_project_access(
            tenant_id=tenant_id,
            project_id=project_id,
        )

        if not self.check_quota(
            tenant_id=tenant_id,
            project_id=project_id,
            cpu_seconds=cpu_seconds,
            gpu_seconds=gpu_seconds,
            jobs=jobs,
        ):
            raise RuntimeError(
                "Tenant quota exceeded."
            )

        usage = self._usage[
            (
                tenant_id,
                project_id,
            )
        ]

        usage.cpu_seconds += cpu_seconds
        usage.gpu_seconds += gpu_seconds
        usage.jobs += jobs

        return usage

    def snapshot(self) -> dict:

        return {
            "tenants": [
                asdict(tenant)
                for tenant in self._tenants.values()
            ],
            "projects": [
                asdict(project)
                for project in self._projects.values()
            ],
            "api_keys": [
                asdict(key)
                for key in self._keys.values()
            ],
            "usage": [
                asdict(usage)
                for usage in self._usage.values()
            ],
        }