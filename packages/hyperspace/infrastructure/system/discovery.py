import os
import platform

import psutil


class SystemDiscovery:
    def cpu(self) -> dict:
        return {
            "name": platform.processor(),
            "cores": psutil.cpu_count(logical=False) or 0,
            "threads": psutil.cpu_count(logical=True) or 0,
            "utilization_percent": psutil.cpu_percent(interval=0.5),
        }

    def memory(self) -> dict:
        memory = psutil.virtual_memory()

        return {
            "total_gb": round(memory.total / (1024 ** 3), 2),
            "available_gb": round(memory.available / (1024 ** 3), 2),
            "utilization_percent": memory.percent,
        }

    def processes(self) -> list[dict]:
        processes = []

        for process in psutil.process_iter(
            ["pid", "name", "status", "memory_percent"]
        ):
            try:
                processes.append(process.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return processes