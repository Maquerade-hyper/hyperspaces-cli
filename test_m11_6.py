from hyperspace.services import (
    FailureDetectionService,
    NodeIsolationService,
    FaultTolerantExecutionService,
)
from hyperspace.core.models import ExecutionRequest


class FakeDispatcher:

    def __init__(self):
        self.calls = []

    def dispatch(self, host, port, request):
        self.calls.append((host, port))

        if host == "FAIL":
            raise ConnectionError("Simulated node failure")

        return type(
            "Result",
            (),
            {
                "success": True,
                "error": None,
            },
        )()


failure_detection = FailureDetectionService(
    missed_threshold=3
)

node_isolation = NodeIsolationService(
    failure_detection=failure_detection
)

service = FaultTolerantExecutionService(
    failure_detection=failure_detection,
    node_isolation=node_isolation,
)

service.dispatcher = FakeDispatcher()

failure_detection.register("NODE-FAIL")
failure_detection.register("NODE-OK")

request = ExecutionRequest(
    execution_id="EXEC-M11-6",
    job_id="JOB-M11-6",
    job_type="test",
    payload={"test": True},
)

nodes = [
    {
        "node_id": "NODE-FAIL",
        "host": "FAIL",
        "port": 8765,
    },
    {
        "node_id": "NODE-OK",
        "host": "OK",
        "port": 8765,
    },
]

result = service.execute(
    request,
    nodes,
)

print("RESULT:", result.success)
print("CALLS:", service.dispatcher.calls)
print("FAIL NODE ISOLATED:", node_isolation.is_isolated("NODE-FAIL"))
print("FAIL NODE ONLINE:", failure_detection.is_online("NODE-FAIL"))
print("OK NODE ISOLATED:", node_isolation.is_isolated("NODE-OK"))
print("OK NODE ONLINE:", failure_detection.is_online("NODE-OK"))
print("RETRY COUNT:", service.retry_service.get_retry_count("JOB-M11-6"))

assert result.success is True
assert node_isolation.is_isolated("NODE-FAIL") is True
assert failure_detection.is_online("NODE-FAIL") is True
assert node_isolation.is_isolated("NODE-OK") is False
assert failure_detection.is_online("NODE-OK") is True
assert service.retry_service.get_retry_count("JOB-M11-6") == 0

print("=== M11.6 FAULT-TOLERANT PIPELINE PASS ===")