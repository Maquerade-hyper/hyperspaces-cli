import json
import socket


class TCPTransport:

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8765,
        resource_registry=None,
        membership=None,
        security=None,
    ):
        from hyperspace.services import (
            MeshMembershipService,
            ResourceRegistryService,
            SecurityIntegrationService,
        )

        self.host = host
        self.port = port

        self.resource_registry = (
            resource_registry
            or ResourceRegistryService()
        )

        self.membership = (
            membership
            or MeshMembershipService()
        )

        self.security = (
            security
            or SecurityIntegrationService()
        )

    # ---------------------------------------------------------
    # CLIENT
    # ---------------------------------------------------------

    def send(
        self,
        host: str,
        port: int,
        message: str,
    ) -> str:

        with socket.create_connection(
            (host, port),
            timeout=5,
        ) as connection:

            connection.sendall(
                message.encode("utf-8")
            )

            return connection.recv(
                65536
            ).decode("utf-8")

    def send_json(
        self,
        host: str,
        port: int,
        payload: dict,
    ) -> dict:

        response = self.send(
            host,
            port,
            json.dumps(payload),
        )

        return json.loads(response)

    # ---------------------------------------------------------
    # SECURITY
    # ---------------------------------------------------------

    def _authenticate_request(
        self,
        payload: dict,
    ) -> str:

        node_id = payload.get(
            "node_id"
        )

        fingerprint = payload.get(
            "fingerprint"
        )

        if not node_id:
            raise PermissionError(
                "Security error: node_id is required."
            )

        if not fingerprint:
            raise PermissionError(
                "Security error: fingerprint is required."
            )

        if not self.security.is_trusted(
            node_id,
            fingerprint,
        ):
            raise PermissionError(
                f"Security error: node "
                f"'{node_id}' is not trusted."
            )

        return node_id

    def _authorize_request(
        self,
        payload: dict,
        permission,
    ) -> str:

        node_id = self._authenticate_request(
            payload
        )

        self.security.require(
            node_id,
            permission,
        )

        return node_id

    # ---------------------------------------------------------
    # SERVER
    # ---------------------------------------------------------

    def start_server(self) -> None:

        from hyperspace.services import (
            Permission,
        )

        with socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM,
        ) as server:

            server.setsockopt(
                socket.SOL_SOCKET,
                socket.SO_REUSEADDR,
                1,
            )

            server.bind(
                (self.host, self.port)
            )

            server.listen()

            print(
                f"Hyperspace TCP server listening "
                f"on {self.host}:{self.port}"
            )

            while True:

                connection, address = (
                    server.accept()
                )

                with connection:

                    data = (
                        connection.recv(
                            65536
                        )
                        .decode("utf-8")
                    )

                    if not data:
                        continue

                    print(
                        f"Received from "
                        f"{address}: {data}"
                    )

                    try:

                        payload = json.loads(
                            data
                        )

                        message_type = (
                            payload.get(
                                "message_type"
                            )
                        )

                        # -------------------------------------------------
                        # NODE HANDSHAKE
                        # -------------------------------------------------

                        if (
                            message_type
                            == "node_handshake"
                        ):

                            node_id = (
                                self._authenticate_request(
                                    payload
                                )
                            )

                            self.security.require(
                                node_id,
                                Permission.NODE_DISCOVERY,
                            )

                            response = {
                                "message_type":
                                    "handshake_ack",
                                "status":
                                    "accepted",
                                "authenticated":
                                    True,
                                "node_id":
                                    node_id,
                            }

                        # -------------------------------------------------
                        # MESH JOIN
                        #
                        # Bootstrap exception:
                        # a brand-new node cannot already be trusted.
                        # MeshJoinService remains responsible for the
                        # invite/join validation.
                        # -------------------------------------------------

                        elif (
                            message_type
                            == "mesh_join_request"
                        ):

                            from hyperspace.services import (
                                MeshJoinService,
                            )

                            response = (
                                MeshJoinService()
                                .process_join_request(
                                    payload
                                )
                            )

                        # -------------------------------------------------
                        # RESOURCE SNAPSHOT
                        # -------------------------------------------------

                        elif (
                            message_type
                            == "resource_snapshot"
                        ):

                            node_id = (
                                self._authorize_request(
                                    payload,
                                    Permission.RESOURCE_USE,
                                )
                            )

                            mesh_id = (
                                payload.get(
                                    "mesh_id"
                                )
                            )

                            resources = (
                                payload.get(
                                    "resources"
                                )
                            )

                            member = (
                                self.membership.get(
                                    node_id
                                )
                            )

                            if member is None:

                                response = {
                                    "message_type":
                                        "resource_snapshot_response",
                                    "accepted":
                                        False,
                                    "node_id":
                                        node_id,
                                    "reason":
                                        "Node is not registered.",
                                }

                            elif (
                                member.status.value
                                != "approved"
                            ):

                                response = {
                                    "message_type":
                                        "resource_snapshot_response",
                                    "accepted":
                                        False,
                                    "node_id":
                                        node_id,
                                    "reason":
                                        "Node is not an approved mesh member.",
                                }

                            elif (
                                member.mesh_id
                                != mesh_id
                            ):

                                response = {
                                    "message_type":
                                        "resource_snapshot_response",
                                    "accepted":
                                        False,
                                    "node_id":
                                        node_id,
                                    "reason":
                                        "Node belongs to another mesh.",
                                }

                            else:

                                self.resource_registry.register(
                                    node_id=node_id,
                                    mesh_id=mesh_id,
                                    resources=resources,
                                )

                                response = {
                                    "message_type":
                                        "resource_snapshot_response",
                                    "accepted":
                                        True,
                                    "node_id":
                                        node_id,
                                    "reason":
                                        "Resource snapshot accepted.",
                                }

                        # -------------------------------------------------
                        # JOB SUBMISSION
                        # -------------------------------------------------

                        elif (
                            message_type
                            == "job_submit"
                        ):

                            node_id = (
                                self._authorize_request(
                                    payload,
                                    Permission.JOB_SUBMIT,
                                )
                            )

                            from hyperspace.services import (
                                JobManagerService,
                            )

                            manager = (
                                JobManagerService()
                            )

                            response = (
                                manager.submit(
                                    payload
                                )
                            )

                        # -------------------------------------------------
                        # EXECUTION REQUEST
                        # -------------------------------------------------

                        elif (
                            message_type
                            == "execution_request"
                        ):

                            node_id = (
                                self._authorize_request(
                                    payload,
                                    Permission.JOB_EXECUTE,
                                )
                            )

                            from hyperspace.core.models import (
                                ExecutionRequest,
                            )

                            from hyperspace.services import (
                                WorkerExecutionService,
                            )

                            request = (
                                ExecutionRequest(
                                    **payload.get(
                                        "request",
                                        {},
                                    )
                                )
                            )

                            result = (
                                WorkerExecutionService()
                                .execute(request)
                            )

                            response = {
                                "message_type":
                                    "execution_result",
                                "node_id":
                                    node_id,
                                "result":
                                    result.model_dump(),
                            }

                        # -------------------------------------------------
                        # UNKNOWN MESSAGE
                        # -------------------------------------------------

                        else:

                            response = {
                                "message_type":
                                    "error",
                                "error":
                                    "Unknown message type.",
                            }

                    except PermissionError as exc:

                        response = {
                            "message_type":
                                "security_error",
                            "accepted":
                                False,
                            "error":
                                str(exc),
                        }

                    except Exception as exc:

                        response = {
                            "message_type":
                                "error",
                            "error":
                                str(exc),
                        }

                    connection.sendall(
                        json.dumps(
                            response,
                            default=str,
                        ).encode("utf-8")
                    )