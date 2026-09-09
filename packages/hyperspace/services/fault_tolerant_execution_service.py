from hyperspace.core.models import (
    ExecutionRequest,
    ExecutionResult,
)

from hyperspace.services.execution_dispatch_service import (
    ExecutionDispatchService,
)

from hyperspace.services.failure_detection_service import (
    FailureDetectionService,
)

from hyperspace.services.job_retry_service import (
    JobRetryService,
)

from hyperspace.services.node_isolation_service import (
    NodeIsolationService,
)


class FaultTolerantExecutionService:

    def __init__(
        self,
        max_retries: int = 3,
        failure_detection=None,
        node_isolation=None,
    ):

        self.dispatcher = (
            ExecutionDispatchService()
        )

        self.failure_detection = (
            failure_detection
            or FailureDetectionService()
        )

        self.node_isolation = (
            node_isolation
            or NodeIsolationService(
                failure_detection=(
                    self.failure_detection
                )
            )
        )

        self.retry_service = (
            JobRetryService(
                max_retries=max_retries
            )
        )


    def execute(
        self,
        request: ExecutionRequest,
        nodes: list[dict],
    ) -> ExecutionResult:

        last_error = (
            "No available nodes."
        )


        # -------------------------------------------------
        # Synchronize discovered nodes with failure detector
        # -------------------------------------------------

        for node in nodes:

            node_id = node.get(
                "node_id"
            )

            if not node_id:
                continue

            if not self.failure_detection.is_online(
                node_id
            ):
                self.failure_detection.register(
                    node_id
                )


        # -------------------------------------------------
        # Determine nodes that are not isolated
        # -------------------------------------------------

        available_node_ids = (
            self.node_isolation.available_nodes(
                [
                    node["node_id"]
                    for node in nodes
                    if node.get("node_id")
                ]
            )
        )


        # -------------------------------------------------
        # Try candidate nodes
        # -------------------------------------------------

        for node in nodes:

            node_id = node.get(
                "node_id"
            )

            if not node_id:
                continue


            if node_id not in available_node_ids:
                continue


            host = node.get(
                "host"
            )

            port = node.get(
                "port"
            )


            if not host or not port:

                last_error = (
                    f"Invalid node connection "
                    f"information for {node_id}."
                )

                continue


            if not self.failure_detection.is_online(
                node_id
            ):

                continue


            try:

                result = (
                    self.dispatcher.dispatch(
                        host,
                        port,
                        request,
                    )
                )


                if result.success:

                    self.failure_detection.reconnect(
                        node_id
                    )

                    self.node_isolation.release(
                        node_id
                    )

                    self.retry_service.reset(
                        request.job_id
                    )

                    return result


                last_error = (
                    result.error
                    or "Execution failed."
                )


                self.failure_detection.record_failure(
                    node_id
                )

                self.node_isolation.isolate(
                    node_id
                )


            except Exception as exc:

                last_error = str(
                    exc
                )


                self.failure_detection.miss_heartbeat(
                    node_id
                )

                self.failure_detection.record_failure(
                    node_id
                )

                self.node_isolation.isolate(
                    node_id
                )

                self.retry_service.record_failure(
                    request.job_id
                )


        return ExecutionResult(

            execution_id=(
                request.execution_id
            ),

            job_id=request.job_id,

            success=False,

            output={},

            error=last_error,

        )