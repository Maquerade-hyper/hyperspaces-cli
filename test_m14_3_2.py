import socket
import threading
import time

from hyperspace.infrastructure.networking.tls_config import (
    TLSConfig,
)

from hyperspace.infrastructure.networking.secure_tcp_transport import (
    SecureTCPTransport,
)

from hyperspace.infrastructure.security.certificate_service import (
    CertificateService,
)

from hyperspace.services.node_identity_service import (
    NodeIdentityService,
)


HOST = "127.0.0.1"
PORT = 9876

node = NodeIdentityService().get_node()

certificates = CertificateService()

cert_path, key_path = (
    certificates.create_node_certificate(
        node.node_id
    )
)

tls = TLSConfig(
    certificate_path=str(cert_path),
    private_key_path=str(key_path),
    ca_certificate_path=str(
        certificates.ca_cert
    ),
)

transport = SecureTCPTransport(tls)

server_ready = threading.Event()
server_done = threading.Event()
server_error = []


def server():

    server_socket = None

    try:

        server_socket, context = (
            transport.create_server_socket(
                HOST,
                PORT,
            )
        )

        server_ready.set()

        raw_connection, address = (
            server_socket.accept()
        )

        print(
            "SERVER ACCEPTED:",
            address,
        )

        with context.wrap_socket(
            raw_connection,
            server_side=True,
        ) as connection:

            print(
                "SERVER TLS:",
                connection.version(),
            )

            data = connection.recv(
                4096
            )

            print(
                "SERVER RECEIVED:",
                data.decode("utf-8"),
            )

            connection.sendall(
                b"TLS-ACK"
            )

            print(
                "SERVER SENT: TLS-ACK"
            )

    except Exception as exc:

        server_error.append(exc)

        print(
            "SERVER ERROR:",
            repr(exc),
        )

    finally:

        if server_socket is not None:
            server_socket.close()

        server_done.set()


thread = threading.Thread(
    target=server,
    daemon=True,
)

thread.start()

if not server_ready.wait(timeout=5):

    raise RuntimeError(
        "TLS server did not start."
    )


client_context = (
    tls.create_client_context()
)

raw_socket = socket.create_connection(
    (HOST, PORT),
    timeout=5,
)

connection = client_context.wrap_socket(
    raw_socket,
    server_hostname=node.node_id,
)

print(
    "CLIENT TLS:",
    connection.version(),
)

print(
    "CLIENT CIPHER:",
    connection.cipher()[0],
)

connection.sendall(
    b"HYPERSPACE-M14-TLS"
)

print(
    "CLIENT SENT: HYPERSPACE-M14-TLS"
)

response = connection.recv(
    4096
).decode("utf-8")

print(
    "CLIENT RECEIVED:",
    response,
)

connection.close()

if not server_done.wait(timeout=5):

    raise RuntimeError(
        "TLS server did not finish."
    )

if server_error:

    raise server_error[0]

assert response == "TLS-ACK"

print(
    "=== M14.3.2 TLS CONNECTION PASS ==="
)