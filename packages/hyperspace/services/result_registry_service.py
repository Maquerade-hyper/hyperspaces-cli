from hyperspace.core.models import ExecutionResult


class ResultRegistryService:

    def __init__(self):
        self._results: dict[str, ExecutionResult] = {}

    def store(
        self,
        result: ExecutionResult,
    ) -> ExecutionResult:

        self._results[result.execution_id] = result

        return result

    def get(
        self,
        execution_id: str,
    ) -> ExecutionResult | None:

        return self._results.get(execution_id)

    def list_results(self) -> list[ExecutionResult]:
        return list(self._results.values())

    def remove(
        self,
        execution_id: str,
    ) -> bool:

        if execution_id not in self._results:
            return False

        del self._results[execution_id]

        return True

    def clear(self) -> None:
        self._results.clear()