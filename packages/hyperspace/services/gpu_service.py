import pynvml

from hyperspace.core.models import GPU


class GPUService:
    def list_gpus(self) -> list[GPU]:
        pynvml.nvmlInit()

        try:
            gpus = []

            for index in range(pynvml.nvmlDeviceGetCount()):
                handle = pynvml.nvmlDeviceGetHandleByIndex(index)

                memory = pynvml.nvmlDeviceGetMemoryInfo(handle)
                utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)

                driver_version = pynvml.nvmlSystemGetDriverVersion()

                if isinstance(driver_version, bytes):
                    driver_version = driver_version.decode()

                gpus.append(
                    GPU(
                        id=index,
                        name=pynvml.nvmlDeviceGetName(handle),
                        vram_total_gb=round(
                            memory.total / (1024 ** 3), 2
                        ),
                        vram_available_gb=round(
                            memory.free / (1024 ** 3), 2
                        ),
                        vram_used_gb=round(
                            memory.used / (1024 ** 3), 2
                        ),
                        utilization_percent=float(utilization.gpu),
                        temperature_c=float(
                            pynvml.nvmlDeviceGetTemperature(
                                handle,
                                pynvml.NVML_TEMPERATURE_GPU,
                            )
                        ),
                        driver_version=driver_version,
                    )
                )

            return gpus

        finally:
            pynvml.nvmlShutdown()