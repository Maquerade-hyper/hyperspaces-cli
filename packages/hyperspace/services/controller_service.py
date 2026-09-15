from hyperspace.core.models import Job, JobAssignment, ExecutionResult

from hyperspace.services.job_manager_service import JobManagerService
from hyperspace.services.resource_pool_service import ResourcePoolService
from hyperspace.services.resource_registry_service import ResourceRegistryService
from hyperspace.services.scheduler_service import SchedulerService
from hyperspace.services.execution_orchestrator_service import (
    ExecutionOrchestratorService,
)
from hyperspace.services.fault_tolerant_execution_service import (
    FaultTolerantExecutionService,
)
from hyperspace.infrastructure.networking.tcp_transport import TCPTransport
from hyperspace.core.models import (
    Job,
    JobAssignment,
    ExecutionRequest,
    ExecutionResult,
)

from hyperspace.services.security_integration_service import (
    SecurityIntegrationService,
)



class ControllerService:

    def __init__(
        self,
        security=None,
    ):
        self.jobs = JobManagerService()

        # ONE shared security service for the entire controller.
        self.security = (
            security or SecurityIntegrationService()
        )

        # One registry shared by the controller's resource pool.
        self.resource_registry = ResourceRegistryService()

        self.resource_pool = ResourcePoolService(
            registry=self.resource_registry
        )

        self.scheduler = SchedulerService()

        # One transport shared by all execution paths.
        self.transport = TCPTransport(
            resource_registry=self.resource_registry,
            membership=self.resource_pool.membership,
            security=self.security,
        )

        self.execution = ExecutionOrchestratorService(
            dispatcher_transport=self.transport,
        )

        self.fault_tolerant_execution = (
            FaultTolerantExecutionService(
                dispatcher_transport=self.transport,
            )
        )
    # ---------------------------------------------------------
    # JOB
    # ---------------------------------------------------------

    def submit_job(self, job: Job) -> Job:
        return self.jobs.submit(job)

    def get_job(self, job_id: str) -> Job | None:
        return self.jobs.get(job_id)

    def list_jobs(self) -> list[Job]:
        return self.jobs.list_jobs()

    # ---------------------------------------------------------
    # RESOURCE POOL
    # ---------------------------------------------------------

    def get_resource_pool(self):
        return self.resource_pool.scheduler_view()

    def _get_scheduler_nodes(self) -> dict[str, dict]:
        view = self.resource_pool.scheduler_view()

        nodes = {}

        for node in view.get("nodes", []):
            node_id = node["node_id"]
            nodes[node_id] = node["resources"]

        return nodes

    # ---------------------------------------------------------
    # SCHEDULING
    # ---------------------------------------------------------

    def schedule_job(
        self,
        job_id: str,
        nodes: dict[str, dict] | None = None,
    ) -> JobAssignment | None:

        job = self.jobs.get(job_id)

        if job is None:
            raise ValueError(
                f"Job not found: {job_id}"
            )

        if nodes is None:
            nodes = self._get_scheduler_nodes()

        return self.scheduler.schedule(
            job,
            nodes
        )

    # ---------------------------------------------------------
    # EXECUTION
    # ---------------------------------------------------------

    def execute_assignment(
        self,
        job_id: str,
        assignment: JobAssignment,
        node: dict,
    ) -> ExecutionResult:

        job = self.jobs.get(job_id)

        if job is None:
            raise ValueError(
                f"Job not found: {job_id}"
            )

        return self.execution.execute_assignment(
            job,
            assignment,
            node,
        )

    # ---------------------------------------------------------
    # FAULT-TOLERANT EXECUTION
    # ---------------------------------------------------------

    def execute_fault_tolerantly(
        self,
        job_id: str,
        candidate_nodes: list[dict],
    ) -> ExecutionResult:

        job = self.jobs.get(
            job_id
        )

        if job is None:
            raise ValueError(
                f"Job not found: {job_id}"
            )

        request = ExecutionRequest(
            execution_id=f"EXEC-{job.job_id}",
            job_id=job.job_id,
            job_type=job.job_type,
            payload=job.payload,
            required_cpu_threads=(
                job.required_cpu_threads
            ),
            required_ram_gb=(
                job.required_ram_gb
            ),
            required_gpu_count=(
                job.required_gpu_count
            ),
            required_vram_gb=(
                job.required_vram_gb
            ),
        )

        result = (
            self.fault_tolerant_execution.execute(
                request,
                candidate_nodes,
            )
        )

        self.execution.results.store(
            result
        )

        if result.success:

            artifact_data = str(
                result.output
            ).encode("utf-8")

            self.execution.create_artifact(
                job_id=job.job_id,
                name=(
                    f"{job.job_id}"
                    f"-fault-tolerant-output.json"
                ),
                data=artifact_data,
                artifact_type=(
                    "fault_tolerant_output"
                ),
                metadata={
                    "execution_id": (
                        result.execution_id
                    ),
                    "job_id": (
                        result.job_id
                    ),
                    "source": (
                        "fault_tolerant_execution"
                    ),
                },
            )

        return result