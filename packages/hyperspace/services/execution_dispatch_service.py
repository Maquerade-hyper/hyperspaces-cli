from hyperspace.core.models import ExecutionRequest, ExecutionResult
from hyperspace.infrastructure.networking.tcp_transport import TCPTransport
from hyperspace.services.security_identity_service import SecurityIdentityService


class ExecutionDispatchService:

    def __init__(self, transport=None, security_identity=None):
        self.transport = transport or TCPTransport()
        self.security_identity = (
            security_identity or SecurityIdentityService()
        )

    def dispatch(
        self,
        host: str,
        port: int,
        request: ExecutionRequest,
    ) -> ExecutionResult:

        identity = self.security_identity.get_identity()

        response = self.transport.send_json(
            host,
            port,
            {
                "message_type": "execution_request",

                # M14 security identity
                "node_id": identity.node_id,
                "fingerprint": identity.fingerprint,

                # Actual execution request
                "request": request.model_dump(mode="json"),
            },
        )

        if not isinstance(response, dict):
            raise RuntimeError(
                "Invalid execution response: response is not an object."
            )

        message_type = response.get("message_type")

        if message_type == "execution_result":

            result_data = response.get("result")

            if not isinstance(result_data, dict):
                raise RuntimeError(
                    "Invalid execution response: missing result."
                )

            try:
                return ExecutionResult.model_validate(
                    result_data
                )
            except Exception as exc:
                raise RuntimeError(
                    f"Invalid execution result: {exc}"
                ) from exc

        if message_type in {
            "security_error",
            "error",
        }:

            error_message = (
                response.get("error")
                or response.get("reason")
                or "Remote execution failed."
            )

            raise RuntimeError(
                f"Remote execution failed: {error_message}"
            )

        raise RuntimeError(
            response.get(
                "reason",
                response.get(
                    "error",
                    f"Invalid execution response: "
                    f"message_type={message_type!r}.",
                ),
            )
        )