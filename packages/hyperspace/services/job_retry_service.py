from hyperspace.core.models import Job, JobStatus
from hyperspace.services.job_registry_service import JobRegistryService


class JobRetryService:

    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self.registry = JobRegistryService()

        self._retry_counts: dict[str, int] = {}

    def record_failure(self, job_id: str) -> int:
        count = self._retry_counts.get(job_id, 0) + 1
        self._retry_counts[job_id] = count

        return count

    def get_retry_count(self, job_id: str) -> int:
        return self._retry_counts.get(job_id, 0)

    def can_retry(self, job_id: str) -> bool:
        return self.get_retry_count(job_id) < self.max_retries

    def retry(self, job_id: str) -> Job | None:

        job = self.registry.get(job_id)

        if job is None:
            return None

        if not self.can_retry(job_id):
            return None

        if job.status not in {
            JobStatus.FAILED,
            JobStatus.QUEUED,
        }:
            raise ValueError(
                f"Job cannot be retried from "
                f"{job.status.value} state."
            )

        self.record_failure(job_id)

        job.status = JobStatus.QUEUED

        jobs = self.registry.list_jobs()
        self.registry.queue.clear()

        for existing_job in jobs:
            if existing_job.job_id == job_id:
                self.registry.queue.enqueue(job)
            else:
                self.registry.queue.enqueue(existing_job)

        return job

    def reset(self, job_id: str) -> None:
        self._retry_counts.pop(job_id, None)

    def clear(self) -> None:
        self._retry_counts.clear()