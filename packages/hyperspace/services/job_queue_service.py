import json
from pathlib import Path

from hyperspace.core.models import Job

from hyperspace.infrastructure.runtime import RuntimePaths


class JobQueueService:
    def __init__(self, storage_path: str | None = None):
        if storage_path is None:
            storage_path = str(
                RuntimePaths().path(
                    "jobs",
                    "job_queue.json",
                )
            )

        # self.storage_path = Path(storage_path)
        self.storage_path = Path(storage_path)

        self.storage_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        if not self.storage_path.exists():
            self._save([])

    def _load(self) -> list[dict]:
        try:
            with self.storage_path.open(
                "r",
                encoding="utf-8"
            ) as file:
                data = json.load(file)

            return data if isinstance(data, list) else []

        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save(self, jobs: list[dict]) -> None:
        with self.storage_path.open(
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(
                jobs,
                file,
                indent=2
            )

    def enqueue(self, job: Job) -> Job:
        jobs = self._load()

        jobs.append(
            job.model_dump(mode="json")
        )

        self._save(jobs)

        return job

    def list_jobs(self) -> list[Job]:
        return [
            Job.model_validate(job)
            for job in self._load()
        ]

    def get_job(self, job_id: str) -> Job | None:
        for job in self.list_jobs():
            if job.job_id == job_id:
                return job

        return None

    def remove_job(self, job_id: str) -> bool:
        jobs = self._load()

        filtered_jobs = [
            job
            for job in jobs
            if job.get("job_id") != job_id
        ]

        if len(filtered_jobs) == len(jobs):
            return False

        self._save(filtered_jobs)

        return True

    def clear(self) -> None:
        self._save([])