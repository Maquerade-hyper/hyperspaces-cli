from __future__ import annotations

import socket
import threading
import uuid
from dataclasses import dataclass


# =========================================================
# RELAY SESSION
# =========================================================

@dataclass
class RelaySession:
    session_id: str
    source_node_id: str
    target_node_id: str
    created_at: float


# =========================================================
# RELAY RESULT
# =========================================================

@dataclass
class RelayResult:
    connected: bool
    session_id: str | None = None
    response: str | None = None
    error: str | None = None


# =========================================================
# RELAY PROTOCOL
# =========================================================

class RelayProtocol:

    CONNECT = "HYPERSPACE_RELAY_CONNECT"
    DATA = "HYPERSPACE_RELAY_DATA"
    CLOSE = "HYPERSPACE_RELAY_CLOSE"
    ACK = "HYPERSPACE_RELAY_ACK"

    @classmethod
    def encode(
        cls,
        message_type: str,
        payload: str = "",
    ) -> bytes:

        return (
            f"{message_type}|{payload}"
        ).encode("utf-8")

    @classmethod
    def decode(
        cls,
        data: bytes,
    ) -> tuple[str, str]:

        message = data.decode(
            "utf-8",
            errors="replace",
        )

        if "|" not in message:
            return message, ""

        message_type, payload = message.split(
            "|",
            1,
        )

        return message_type, payload


# =========================================================
# RELAY SERVER
# =========================================================

class RelayServer:

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 0,
    ):

        self.host = host
        self.port = port

        self._socket: socket.socket | None = None
        self._thread: threading.Thread | None = None
        self._running = False

        self._sessions: dict[
            str,
            RelaySession,
        ] = {}

        self._lock = threading.RLock()

    @property
    def address(self) -> tuple[str, int] | None:

        if self._socket is None:
            return None

        return self._socket.getsockname()

    def start(self) -> tuple[str, int]:

        if self._running:
            return self.address

        self._socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM,
        )

        self._socket.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1,
        )

        self._socket.bind(
            (
                self.host,
                self.port,
            )
        )

        self._socket.listen(16)

        self._running = True

        self._thread = threading.Thread(
            target=self._accept_loop,
            daemon=True,
        )

        self._thread.start()

        return self.address

    def stop(self) -> None:

        self._running = False

        if self._socket is not None:

            try:
                self._socket.close()
            except OSError:
                pass

            self._socket = None

    def _accept_loop(self) -> None:

        while self._running:

            try:

                connection, _address = (
                    self._socket.accept()
                )

            except OSError:

                if not self._running:
                    break

                continue

            thread = threading.Thread(
                target=self._handle_client,
                args=(connection,),
                daemon=True,
            )

            thread.start()

    def _handle_client(
        self,
        connection: socket.socket,
    ) -> None:

        try:

            connection.settimeout(5)

            data = connection.recv(
                65535
            )

            if not data:
                return

            message_type, payload = (
                RelayProtocol.decode(data)
            )

            if message_type == RelayProtocol.CONNECT:

                session_id = str(
                    uuid.uuid4()
                )

                parts = payload.split(
                    ":",
                    1,
                )

                source_node_id = (
                    parts[0]
                    if parts
                    else ""
                )

                target_node_id = (
                    parts[1]
                    if len(parts) > 1
                    else ""
                )

                session = RelaySession(
                    session_id=session_id,
                    source_node_id=source_node_id,
                    target_node_id=target_node_id,
                    created_at=__import__(
                        "time"
                    ).time(),
                )

                with self._lock:
                    self._sessions[
                        session_id
                    ] = session

                response = RelayProtocol.encode(
                    RelayProtocol.ACK,
                    session_id,
                )

                connection.sendall(
                    response
                )

                return

            if message_type == RelayProtocol.CLOSE:

                session_id = payload.strip()

                with self._lock:
                    self._sessions.pop(
                        session_id,
                        None,
                    )

                connection.sendall(
                    RelayProtocol.encode(
                        RelayProtocol.ACK,
                        session_id,
                    )
                )

                return

            connection.sendall(
                RelayProtocol.encode(
                    "HYPERSPACE_RELAY_ERROR",
                    "Unknown relay message.",
                )
            )

        except Exception as exc:

            try:
                connection.sendall(
                    RelayProtocol.encode(
                        "HYPERSPACE_RELAY_ERROR",
                        str(exc),
                    )
                )
            except Exception:
                pass

        finally:

            try:
                connection.close()
            except OSError:
                pass

    def session_count(self) -> int:

        with self._lock:
            return len(self._sessions)

    def has_session(
        self,
        session_id: str,
    ) -> bool:

        with self._lock:
            return session_id in self._sessions


# =========================================================
# RELAY CLIENT
# =========================================================

class RelayClient:

    def connect(
        self,
        host: str,
        port: int,
        source_node_id: str,
        target_node_id: str,
        timeout: float = 5.0,
    ) -> RelayResult:

        sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM,
        )

        sock.settimeout(timeout)

        try:

            sock.connect(
                (
                    host,
                    port,
                )
            )

            payload = (
                f"{source_node_id}:"
                f"{target_node_id}"
            )

            sock.sendall(
                RelayProtocol.encode(
                    RelayProtocol.CONNECT,
                    payload,
                )
            )

            data = sock.recv(
                65535
            )

            message_type, response = (
                RelayProtocol.decode(data)
            )

            if message_type != RelayProtocol.ACK:

                return RelayResult(
                    connected=False,
                    error=response
                    or "Relay connection rejected.",
                )

            return RelayResult(
                connected=True,
                session_id=response,
                response="Relay session established.",
            )

        except Exception as exc:

            return RelayResult(
                connected=False,
                error=str(exc),
            )

        finally:

            sock.close()

    def close(
        self,
        host: str,
        port: int,
        session_id: str,
        timeout: float = 5.0,
    ) -> RelayResult:

        sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM,
        )

        sock.settimeout(timeout)

        try:

            sock.connect(
                (
                    host,
                    port,
                )
            )

            sock.sendall(
                RelayProtocol.encode(
                    RelayProtocol.CLOSE,
                    session_id,
                )
            )

            data = sock.recv(
                65535
            )

            message_type, response = (
                RelayProtocol.decode(data)
            )

            return RelayResult(
                connected=(
                    message_type
                    == RelayProtocol.ACK
                ),
                session_id=session_id,
                response=response,
            )

        except Exception as exc:

            return RelayResult(
                connected=False,
                session_id=session_id,
                error=str(exc),
            )

        finally:

            sock.close()


# =========================================================
# RELAY CONNECTION MANAGER
# =========================================================

@dataclass
class RelayFallbackResult:
    direct_connected: bool
    relay_connected: bool
    connection_type: str
    session_id: str | None = None
    error: str | None = None


class RelayConnectionManager:

    def __init__(
        self,
        relay_client: RelayClient | None = None,
    ):

        self.relay_client = (
            relay_client
            or RelayClient()
        )

    def connect_relay(
        self,
        relay_host: str,
        relay_port: int,
        source_node_id: str,
        target_node_id: str,
    ) -> RelayResult:

        return self.relay_client.connect(
            host=relay_host,
            port=relay_port,
            source_node_id=source_node_id,
            target_node_id=target_node_id,
        )

    def connect_with_fallback(
        self,
        direct_connector,
        relay_host: str,
        relay_port: int,
        source_node_id: str,
        target_node_id: str,
    ) -> RelayFallbackResult:

        # -----------------------------------------------------
        # DIRECT PATH
        # -----------------------------------------------------

        try:

            direct_result = direct_connector()

            if direct_result:

                return RelayFallbackResult(
                    direct_connected=True,
                    relay_connected=False,
                    connection_type="direct",
                )

        except Exception:
            pass

        # -----------------------------------------------------
        # RELAY FALLBACK
        # -----------------------------------------------------

        relay_result = self.connect_relay(
            relay_host=relay_host,
            relay_port=relay_port,
            source_node_id=source_node_id,
            target_node_id=target_node_id,
        )

        if relay_result.connected:

            return RelayFallbackResult(
                direct_connected=False,
                relay_connected=True,
                connection_type="relay",
                session_id=relay_result.session_id,
            )

        return RelayFallbackResult(
            direct_connected=False,
            relay_connected=False,
            connection_type="failed",
            error=relay_result.error,
        )


# =========================================================
# PUBLIC HELPERS
# =========================================================

def create_relay_server(
    host: str = "127.0.0.1",
    port: int = 0,
) -> RelayServer:

    return RelayServer(
        host=host,
        port=port,
    )


def create_relay_client() -> RelayClient:

    return RelayClient()