from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from hyperspace.services.controller_service import ControllerService
from hyperspace.services.node_identity_service import NodeIdentityService
from hyperspace.services.node_registry_service import NodeRegistryService
from hyperspace.services.resource_provider_service import ResourceProviderService
from hyperspace.services.mesh_membership_service import MeshMembershipService

from hyperspace.services.security_identity_service import (
    SecurityIdentityService,
)
from hyperspace.services.security_integration_service import (
    SecurityIntegrationService,
)
from hyperspace.services.permission_service import Role

from hyperspace.core.models import Job

from hyperspace.services import DistributedPartitionService


# =========================================================
# APPLICATION
# =========================================================

app = FastAPI(
    title="Hyperspace Controller API",
    description="Controller API for the Hyperspace distributed compute mesh.",
    version="0.5.0",
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:8001",
        "http://localhost:8001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# SECURITY
# =========================================================

security_identity = SecurityIdentityService()
security = SecurityIntegrationService()


# =========================================================
# CONTROLLER
# =========================================================

controller = ControllerService(
    security=security,
)

node_identity = NodeIdentityService()
node_registry = NodeRegistryService()
resource_provider = ResourceProviderService()

resource_registry = controller.resource_registry

membership = MeshMembershipService()


# =========================================================
# LOCAL CONTROLLER NODE BOOTSTRAP
# =========================================================

def bootstrap_local_node():
    """
    Bootstrap the local Hyperspace controller node.

    Responsibilities:
        - Load/create node identity
        - Load/create security identity
        - Register controller security identity
        - Register node
        - Restore mesh membership
        - Register local resources
    """

    # -----------------------------------------------------
    # Node identity
    # -----------------------------------------------------

    node = node_identity.get_node()

    # -----------------------------------------------------
    # Security identity
    # -----------------------------------------------------

    identity = security_identity.get_identity()

    # Register the local controller using the SAME
    # SecurityIntegrationService instance used by
    # ControllerService -> TCPTransport.
    security.register_node(
        identity,
        Role.CONTROLLER,
    )
    
    print(
        f"Security trusted: "
        f"{security.is_trusted(identity.node_id, identity.fingerprint)}"
    )

    print(
        f"Trusted nodes: "
        f"{security.authentication.trusted_nodes()}"
    )

    # -----------------------------------------------------
    # Node registry
    # -----------------------------------------------------

    node_registry.register(node)

    # -----------------------------------------------------
    # Mesh membership
    # -----------------------------------------------------

    member = membership.get(
        node.node_id
    )

    if member is None:
        member = membership.request_join(
            mesh_id="UNASSIGNED",
            node_id=node.node_id,
            hostname=node.hostname,
            platform=node.platform,
            ip_address=node.ip_address,
            port=node.port,
        )

    # -----------------------------------------------------
    # Resource snapshot
    # -----------------------------------------------------

    snapshot = resource_provider.get_snapshot()

    resources = (
        snapshot.model_dump()
        if hasattr(snapshot, "model_dump")
        else snapshot
    )

    # -----------------------------------------------------
    # Resource registry
    # -----------------------------------------------------

    resource_registry.register(
        node_id=node.node_id,
        mesh_id=member.mesh_id,
        resources=resources,
    )

    return node


# Bootstrap local controller node when API starts.

local_node = bootstrap_local_node()


# =========================================================
# ROOT
# =========================================================

@app.get("/")
def root():
    return {
        "service": "hyperspace-controller",
        "status": "online",
        "version": "0.5.0",
        "node_id": local_node.node_id,
    }


# =========================================================
# HEALTH
# =========================================================

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "controller": "online",
        "node_id": local_node.node_id,
    }


# =========================================================
# NODES
# =========================================================

@app.get("/api/nodes")
def list_nodes():

    nodes = node_registry.list_nodes()

    return {
        "count": len(nodes),
        "nodes": [
            node.model_dump()
            if hasattr(node, "model_dump")
            else node
            for node in nodes
        ],
    }


@app.get("/api/nodes/{node_id}")
def get_node(
    node_id: str,
):

    node = node_registry.get(
        node_id
    )

    if node is None:
        raise HTTPException(
            status_code=404,
            detail=f"Node '{node_id}' not found.",
        )

    return (
        node.model_dump()
        if hasattr(node, "model_dump")
        else node
    )


# =========================================================
# RESOURCES
# =========================================================

@app.get("/api/resources")
def list_resources():

    resources = resource_registry.list_all()

    return {
        "count": len(resources),
        "resources": resources,
    }


@app.get("/api/resources/available")
def available_resources():

    resources = (
        controller.resource_pool
        .available_resources()
    )

    return (
        resources.model_dump()
        if hasattr(resources, "model_dump")
        else resources
    )


@app.get("/api/resources/cluster")
def cluster_resources():

    resources = (
        controller.resource_pool
        .cluster_totals()
    )

    return (
        resources.model_dump()
        if hasattr(resources, "model_dump")
        else resources
    )


# =========================================================
# JOBS
# =========================================================

@app.post("/api/jobs")
def submit_job(
    payload: dict,
):

    try:

        job = Job(
            **payload
        )

        result = controller.jobs.submit(
            job
        )

        if hasattr(
            result,
            "model_dump",
        ):
            return result.model_dump()

        return result

    except Exception as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@app.get("/api/jobs")
def list_jobs():

    jobs = controller.list_jobs()

    return {
        "count": len(jobs),
        "jobs": [
            job.model_dump()
            if hasattr(
                job,
                "model_dump",
            )
            else job
            for job in jobs
        ],
    }


@app.get("/api/jobs/{job_id}")
def get_job(
    job_id: str,
):

    job = controller.get_job(
        job_id
    )

    if job is None:

        raise HTTPException(
            status_code=404,
            detail=f"Job '{job_id}' not found.",
        )

    return (
        job.model_dump()
        if hasattr(
            job,
            "model_dump",
        )
        else job
    )


@app.post("/api/jobs/{job_id}/cancel")
def cancel_job(
    job_id: str,
):

    try:

        result = controller.jobs.cancel(
            job_id
        )

        return (
            result.model_dump()
            if hasattr(
                result,
                "model_dump",
            )
            else result
        )

    except Exception as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# =========================================================
# SCHEDULER
# =========================================================

@app.post("/api/scheduler/assign")
def assign_job(
    payload: dict,
):

    try:

        job_id = payload.get(
            "job_id"
        )

        if not job_id:

            raise ValueError(
                "job_id is required."
            )

        assignment = controller.schedule_job(
            job_id=job_id
        )

        if assignment is None:

            raise ValueError(
                "No suitable node was found."
            )

        return (
            assignment.model_dump()
            if hasattr(
                assignment,
                "model_dump",
            )
            else assignment
        )

    except Exception as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# =========================================================
# EXECUTION
# =========================================================

@app.post("/api/execution")
def execute_job(
    payload: dict,
):

    try:

        job_id = payload.get(
            "job_id"
        )

        assignment = payload.get(
            "assignment"
        )

        if not job_id:

            raise ValueError(
                "job_id is required."
            )

        if not assignment:

            raise ValueError(
                "assignment is required."
            )

        node_id = assignment.get(
            "node_id"
        )

        if not node_id:

            raise ValueError(
                "assignment.node_id is required."
            )

        node = next(
            (
                n
                for n in node_registry.list_all()
                if n.node_id == node_id
            ),
            None,
        )

        if node is None:

            raise ValueError(
                f"Node not found: {node_id}"
            )

        node_data = {
            "node_id": node.node_id,
            "host": node.ip_address,
            "port": node.port,
        }

        result = controller.execute_assignment(
            job_id=job_id,
            assignment=assignment,
            node=node_data,
        )

        if hasattr(
            result,
            "model_dump",
        ):

            result_data = result.model_dump(
                mode="json"
            )

        else:

            result_data = result

        artifacts = (
            controller.execution
            .get_job_artifacts(
                job_id
            )
        )

        artifact_data = []

        for artifact in artifacts:

            if hasattr(
                artifact,
                "model_dump",
            ):

                artifact_data.append(
                    artifact.model_dump(
                        mode="json"
                    )
                )

            else:

                artifact_data.append(
                    artifact
                )

        result_data["artifacts"] = (
            artifact_data
        )

        result_data["artifact"] = (
            artifact_data[-1]
            if artifact_data
            else None
        )

        return result_data

    except Exception as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# =========================================================
# FAULT-TOLERANT EXECUTION
# =========================================================

@app.post(
    "/api/execution/fault-tolerant"
)
def execute_fault_tolerantly(
    payload: dict,
):

    try:

        job_id = payload.get(
            "job_id"
        )

        candidate_nodes = payload.get(
            "candidate_nodes",
            [],
        )

        if not job_id:

            raise ValueError(
                "job_id is required."
            )

        result = (
            controller.execute_fault_tolerantly(
                job_id=job_id,
                candidate_nodes=candidate_nodes,
            )
        )

        if hasattr(
            result,
            "model_dump",
        ):

            result_data = result.model_dump(
                mode="json"
            )

        else:

            result_data = result

        artifacts = (
            controller.execution
            .get_job_artifacts(
                job_id
            )
        )

        artifact_data = []

        for artifact in artifacts:

            if hasattr(
                artifact,
                "model_dump",
            ):

                artifact_data.append(
                    artifact.model_dump(
                        mode="json"
                    )
                )

            else:

                artifact_data.append(
                    artifact
                )

        result_data["artifacts"] = (
            artifact_data
        )

        result_data["artifact"] = (
            artifact_data[-1]
            if artifact_data
            else None
        )

        return result_data

    except Exception as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# =========================================================
# DISTRIBUTED EXECUTION
# =========================================================

@app.post(
    "/api/execution/distributed"
)
def execute_distributed(
    payload: dict,
):

    try:

        job_id = payload.get(
            "job_id"
        )

        partition_count = int(
            payload.get(
                "partition_count",
                1,
            )
        )

        if not job_id:

            raise ValueError(
                "job_id is required."
            )

        if partition_count < 1:

            raise ValueError(
                "partition_count must be at least 1."
            )

        job = controller.jobs.get(
            job_id
        )

        if job is None:

            raise ValueError(
                f"Job not found: {job_id}"
            )

        partition_service = (
            DistributedPartitionService()
        )

        execution = (
            partition_service.create_execution(
                job=job,
                partition_count=partition_count,
            )
        )

        registered_nodes = (
            node_registry.list_all()
        )

        available_nodes = {}

        for node in registered_nodes:

            available_nodes[
                node.node_id
            ] = {
                "node_id": node.node_id,
                "host": node.ip_address,
                "port": node.port,
            }

        requested_node_ids = payload.get(
            "node_ids"
        )

        if requested_node_ids:

            selected_node_ids = [
                node_id
                for node_id in requested_node_ids
                if node_id in available_nodes
            ]

        else:

            selected_node_ids = list(
                available_nodes.keys()
            )

        if not selected_node_ids:

            raise ValueError(
                "No valid nodes available."
            )

        for index, partition in enumerate(
            execution.partitions
        ):

            node_id = selected_node_ids[
                index
                % len(selected_node_ids)
            ]

            partition.assigned_node_id = (
                node_id
            )

            partition.status = (
                "assigned"
            )

        nodes = {
            node_id:
                available_nodes[node_id]
            for node_id
            in selected_node_ids
        }

        results = (
            controller.execution
            .execute_distributed(
                execution=execution,
                nodes=nodes,
            )
        )

        result_data = []

        for result in results:

            if hasattr(
                result,
                "model_dump",
            ):

                result_data.append(
                    result.model_dump(
                        mode="json"
                    )
                )

            else:

                result_data.append(
                    result
                )

        artifacts = (
            controller.execution
            .get_job_artifacts(
                job_id
            )
        )

        artifact_data = []

        for artifact in artifacts:

            if hasattr(
                artifact,
                "model_dump",
            ):

                artifact_data.append(
                    artifact.model_dump(
                        mode="json"
                    )
                )

            else:

                artifact_data.append(
                    artifact
                )

        return {
            "execution_id":
                execution.execution_id,

            "job_id":
                job_id,

            "total_partitions":
                execution.total_partitions,

            "partitions": [
                partition.model_dump(
                    mode="json"
                )
                for partition
                in execution.partitions
            ],

            "results":
                result_data,

            "artifacts":
                artifact_data,

            "artifact":
                (
                    artifact_data[-1]
                    if artifact_data
                    else None
                ),
        }

    except Exception as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# =========================================================
# ARTIFACTS
# =========================================================

@app.get("/api/artifacts")
def list_artifacts():

    try:

        artifacts = (
            controller.execution
            .artifacts
            .list_artifacts()
        )

        return [
            artifact.model_dump(
                mode="json"
            )
            if hasattr(
                artifact,
                "model_dump",
            )
            else artifact
            for artifact
            in artifacts
        ]

    except Exception as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@app.get(
    "/api/artifacts/{artifact_id}"
)
def get_artifact(
    artifact_id: str,
):

    try:

        artifact = (
            controller.execution
            .artifacts
            .get(
                artifact_id
            )
        )

        if artifact is None:

            raise ValueError(
                f"Artifact not found: "
                f"{artifact_id}"
            )

        if hasattr(
            artifact,
            "model_dump",
        ):

            return artifact.model_dump(
                mode="json"
            )

        return artifact

    except Exception as exc:

        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )


@app.get(
    "/api/jobs/{job_id}/artifacts"
)
def list_job_artifacts(
    job_id: str,
):

    try:

        artifacts = (
            controller.execution
            .get_job_artifacts(
                job_id
            )
        )

        return [
            artifact.model_dump(
                mode="json"
            )
            if hasattr(
                artifact,
                "model_dump",
            )
            else artifact
            for artifact
            in artifacts
        ]

    except Exception as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# =========================================================
# GPU
# =========================================================

@app.get("/api/gpus")
def list_gpus():

    try:

        controller_gpus = (
            controller.execution
            .gpu_registry
            .list_all()
        )

        result = []

        for key, gpu in (
            controller.execution
            .gpu_registry
            ._gpus
            .items()
        ):

            node_id = key.rsplit(
                ":",
                1
            )[0]

            if hasattr(
                gpu,
                "model_dump",
            ):

                gpu_data = gpu.model_dump(
                    mode="json"
                )

            else:

                gpu_data = dict(
                    gpu
                )

            gpu_data["node_id"] = (
                node_id
            )

            result.append(
                gpu_data
            )

        return result

    except Exception as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@app.get(
    "/api/gpus/{node_id}/{gpu_id}"
)
def get_gpu(
    node_id: str,
    gpu_id: int,
):

    try:

        gpu = (
            controller.execution
            .gpu_registry
            .get(
                node_id,
                gpu_id,
            )
        )

        if gpu is None:

            raise ValueError(
                f"GPU not found: "
                f"{node_id}:{gpu_id}"
            )

        if hasattr(
            gpu,
            "model_dump",
        ):

            gpu_data = gpu.model_dump(
                mode="json"
            )

        else:

            gpu_data = dict(
                gpu
            )

        gpu_data["node_id"] = (
            node_id
        )

        return gpu_data

    except Exception as exc:

        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )


# =========================================================
# API INFORMATION
# =========================================================

@app.get("/api")
def api_info():

    return {
        "service":
            "hyperspace-controller",

        "version":
            "0.5.0",

        "endpoints": {

            "nodes": [
                "GET /api/nodes",
                "GET /api/nodes/{node_id}",
            ],

            "resources": [
                "GET /api/resources",
                "GET /api/resources/available",
                "GET /api/resources/cluster",
            ],

            "jobs": [
                "POST /api/jobs",
                "GET /api/jobs",
                "GET /api/jobs/{job_id}",
                "POST /api/jobs/{job_id}/cancel",
            ],

            "scheduler": [
                "POST /api/scheduler/assign",
            ],

            "execution": [
                "POST /api/execution",
                "POST /api/execution/distributed",
                "POST /api/execution/fault-tolerant",
            ],
        },
    }


# =========================================================
# DIRECT STARTUP
# =========================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
    )