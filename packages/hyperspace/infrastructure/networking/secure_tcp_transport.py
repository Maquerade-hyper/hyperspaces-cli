import json
import socket

from hyperspace.infrastructure.networking.tls_config import (
    TLSConfig,
)


class SecureTCPTransport:

    def __init__(
        self,
        tls: TLSConfig,
    ):
        self.tls = tls

    def send_json(
        self,
        host: str,
        port: int,
        payload: dict,
    ) -> dict:

        context = (
            self.tls.create_client_context()
        )

        raw_socket = socket.create_connection(
            (host, port),
            timeout=5,
        )

        with context.wrap_socket(
            raw_socket,
            server_hostname=host,
        ) as connection:

            connection.sendall(
                json.dumps(
                    payload
                ).encode("utf-8")
            )

            response = connection.recv(
                65536
            ).decode("utf-8")

        return json.loads(response)

    def create_server_socket(
        self,
        host: str,
        port: int,
    ):

        context = (
            self.tls.create_server_context()
        )

        server = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM,
        )

        server.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1,
        )

        server.bind(
            (host, port)
        )

        server.listen()

        return server, context