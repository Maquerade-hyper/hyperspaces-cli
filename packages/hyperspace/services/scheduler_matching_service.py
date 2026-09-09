from hyperspace.core.models import Job


class SchedulerMatchingService:

    def can_run(
        self,
        job: Job,
        resources: dict,
    ) -> bool:

        cpu = resources.get("cpu", {})
        ram = resources.get("ram", {})
        gpus = resources.get("gpus", [])

        available_threads = cpu.get("threads", 0)
        available_ram = ram.get("available_gb", 0.0)

        if available_threads < job.required_cpu_threads:
            return False

        if available_ram < job.required_ram_gb:
            return False

        available_gpus = [
            gpu
            for gpu in gpus
            if gpu.get("available", True)
        ]

        if len(available_gpus) < job.required_gpu_count:
            return False

        if job.required_gpu_count > 0:

            selected = self.select_gpus(
                job,
                resources,
            )

            if len(selected) < job.required_gpu_count:
                return False

        return True

    def select_gpus(
        self,
        job: Job,
        resources: dict,
    ) -> list[dict]:

        gpus = resources.get("gpus", [])

        available_gpus = [
            gpu
            for gpu in gpus
            if gpu.get("available", True)
            and gpu.get(
                "vram_available_gb",
                0.0,
            ) >= job.required_vram_gb
        ]

        available_gpus.sort(
            key=lambda gpu: gpu.get(
                "vram_available_gb",
                0.0,
            ),
            reverse=True,
        )

        return available_gpus[
            :job.required_gpu_count
        ]

    def explain(
        self,
        job: Job,
        resources: dict,
    ) -> str:

        if not self.can_run(
            job,
            resources,
        ):
            return "Insufficient resources."

        if job.required_gpu_count > 0:

            selected = self.select_gpus(
                job,
                resources,
            )

            return (
                "Node can run job using GPU(s): "
                + ", ".join(
                    str(gpu.get("id"))
                    for gpu in selected
                )
            )

        return "Node can run job."