from hyperspace.core.models import Job, NodeScore


class SchedulerScoringService:

    def score(
        self,
        job: Job,
        resources: dict,
        node_id: str,
    ) -> NodeScore:

        cpu = resources.get("cpu", {})
        ram = resources.get("ram", {})
        gpus = resources.get("gpus", [])

        cpu_available = cpu.get("threads", 0)
        ram_available = ram.get("available_gb", 0.0)

        cpu_score = (
            min(
                cpu_available / max(job.required_cpu_threads, 1),
                1.0,
            )
            if job.required_cpu_threads > 0
            else 1.0
        )

        ram_score = (
            min(
                ram_available / max(job.required_ram_gb, 0.1),
                1.0,
            )
            if job.required_ram_gb > 0
            else 1.0
        )

        gpu_score = (
            min(
                len(gpus) / job.required_gpu_count,
                1.0,
            )
            if job.required_gpu_count > 0
            else 1.0
        )

        available_vram = sum(
            gpu.get("vram_available_gb", 0.0)
            for gpu in gpus
        )

        vram_score = (
            min(
                available_vram / max(job.required_vram_gb, 0.1),
                1.0,
            )
            if job.required_vram_gb > 0
            else 1.0
        )

        total_score = (
            cpu_score * 0.25
            + ram_score * 0.25
            + gpu_score * 0.20
            + vram_score * 0.30
        )

        return NodeScore(
            node_id=node_id,
            cpu_score=cpu_score,
            ram_score=ram_score,
            gpu_score=gpu_score,
            vram_score=vram_score,
            total_score=total_score,
        )