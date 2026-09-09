from hyperspace.core.models import Job, JobStatus
from hyperspace.services.job_registry_service import JobRegistryService


class JobManagerService:
    def __init__(self):
        self.registry = JobRegistryService()

    def submit(self, job: Job) -> Job:
        return self.registry.register(job)

    def get(self, job_id: str) -> Job | None:
        return self.registry.get(job_id)

    def list_jobs(self) -> list[Job]:
        return self.registry.list_jobs()

    def start(self, job_id: str) -> Job | None:
        return self.registry.update_status(
            job_id,
            JobStatus.RUNNING,
        )

    def complete(self, job_id: str) -> Job | None:
        return self.registry.update_status(
            job_id,
            JobStatus.COMPLETED,
        )

    def fail(self, job_id: str) -> Job | None:
        return self.registry.update_status(
            job_id,
            JobStatus.FAILED,
        )

    def cancel(self, job_id: str) -> Job | None:
        return self.registry.update_status(
            job_id,
            JobStatus.CANCELLED,
        )

    def queued(self) -> list[Job]:
        return self.registry.queued_jobs()

    def running(self) -> list[Job]:
        return self.registry.running_jobs()

    def completed(self) -> list[Job]:
        return self.registry.completed_jobs()

    def failed(self) -> list[Job]:
        return self.registry.failed_jobs()

    def cancelled(self) -> list[Job]:
        return self.registry.cancelled_jobs()