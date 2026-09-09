from hyperspace.core.models import (
    ExecutionRequest,
    ExecutionResult,
)


class WorkerExecutionService:

    def execute(
        self,
        request: ExecutionRequest,
    ) -> ExecutionResult:

        try:
            if request.job_type == "test":
                return ExecutionResult(
                    execution_id=request.execution_id,
                    job_id=request.job_id,
                    success=True,
                    output={
                        "result": "Job executed successfully.",
                        "payload": request.payload,
                    },
                )

            return ExecutionResult(
                execution_id=request.execution_id,
                job_id=request.job_id,
                success=False,
                error=f"Unsupported job type: {request.job_type}",
            )

        except Exception as exc:
            return ExecutionResult(
                execution_id=request.execution_id,
                job_id=request.job_id,
                success=False,
                error=str(exc),
            )