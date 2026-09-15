from __future__ import annotations

from hyperspace.services.relay_service import (
    RelayClient,
    RelayConnectionManager,
    RelayProtocol,
    RelayServer,
)


def main() -> None:

    print("=" * 60)
    print("HYPERSPACE M23 RELAY / FALLBACK")
    print("=" * 60)

    # =====================================================
    # M23.1 RELAY PROTOCOL
    # =====================================================

    print()
    print("[M23.1] Testing relay protocol...")

    encoded = RelayProtocol.encode(
        RelayProtocol.CONNECT,
        "node-a:node-b",
    )

    message_type, payload = (
        RelayProtocol.decode(encoded)
    )

    if message_type != RelayProtocol.CONNECT:
        raise RuntimeError(
            "Relay protocol type mismatch."
        )

    if payload != "node-a:node-b":
        raise RuntimeError(
            "Relay protocol payload mismatch."
        )

    print("    ENCODE: PASS")
    print("    DECODE: PASS")
    print("    RELAY PROTOCOL: PASS")

    # =====================================================
    # M23.2 RELAY SERVER
    # =====================================================

    print()
    print("[M23.2] Starting relay server...")

    server = RelayServer(
        host="127.0.0.1",
        port=0,
    )

    address = server.start()

    if not address:
        raise RuntimeError(
            "Relay server failed to start."
        )

    relay_host, relay_port = address

    print(
        "    RELAY ADDRESS:",
        f"{relay_host}:{relay_port}",
    )

    print("    RELAY SERVER: PASS")

    # =====================================================
    # M23.3 RELAY CLIENT
    # =====================================================

    print()
    print("[M23.3] Connecting relay client...")

    client = RelayClient()

    connection = client.connect(
        host=relay_host,
        port=relay_port,
        source_node_id="node-a",
        target_node_id="node-b",
    )

    print(
        "    CONNECTED:",
        connection.connected,
    )

    print(
        "    SESSION:",
        connection.session_id,
    )

    if connection.error:
        print(
            "    ERROR:",
            connection.error,
        )

    if not connection.connected:
        server.stop()

        raise RuntimeError(
            "Relay client connection failed."
        )

    if not connection.session_id:
        server.stop()

        raise RuntimeError(
            "Relay session ID missing."
        )

    if not server.has_session(
        connection.session_id
    ):
        server.stop()

        raise RuntimeError(
            "Relay server did not create session."
        )

    print("    SESSION CREATION: PASS")
    print("    RELAY CLIENT: PASS")

    # =====================================================
    # M23.4 DIRECT → RELAY FALLBACK
    # =====================================================

    print()
    print("[M23.4] Testing direct → relay fallback...")

    manager = RelayConnectionManager(
        relay_client=client,
    )

    fallback = (
        manager.connect_with_fallback(
            direct_connector=lambda: False,
            relay_host=relay_host,
            relay_port=relay_port,
            source_node_id="node-a",
            target_node_id="node-b",
        )
    )

    print(
        "    DIRECT:",
        fallback.direct_connected,
    )

    print(
        "    RELAY:",
        fallback.relay_connected,
    )

    print(
        "    CONNECTION TYPE:",
        fallback.connection_type,
    )

    print(
        "    SESSION:",
        fallback.session_id,
    )

    if not fallback.relay_connected:
        server.stop()

        raise RuntimeError(
            "Relay fallback failed."
        )

    if fallback.connection_type != "relay":
        server.stop()

        raise RuntimeError(
            "Fallback did not select relay."
        )

    print("    DIRECT FAILURE DETECTED: PASS")
    print("    RELAY FALLBACK: PASS")

    # =====================================================
    # DIRECT PATH PREFERENCE
    # =====================================================

    print()
    print("[M23.4] Testing direct-path preference...")

    direct = (
        manager.connect_with_fallback(
            direct_connector=lambda: True,
            relay_host=relay_host,
            relay_port=relay_port,
            source_node_id="node-a",
            target_node_id="node-b",
        )
    )

    print(
        "    DIRECT:",
        direct.direct_connected,
    )

    print(
        "    RELAY:",
        direct.relay_connected,
    )

    print(
        "    CONNECTION TYPE:",
        direct.connection_type,
    )

    if not direct.direct_connected:
        server.stop()

        raise RuntimeError(
            "Direct path was not preferred."
        )

    if direct.connection_type != "direct":
        server.stop()

        raise RuntimeError(
            "Relay was incorrectly selected."
        )

    print("    DIRECT PATH PREFERENCE: PASS")

    # =====================================================
    # CLOSE SESSION
    # =====================================================

    print()
    print("[M23.5] Closing relay session...")

    closed = client.close(
        host=relay_host,
        port=relay_port,
        session_id=connection.session_id,
    )

    print(
        "    CLOSED:",
        closed.connected,
    )

    if not closed.connected:
        server.stop()

        raise RuntimeError(
            "Relay session close failed."
        )

    print("    SESSION CLOSE: PASS")

    # =====================================================
    # FINAL
    # =====================================================

    server.stop()

    print()
    print("=" * 60)
    print("M23 RESULT: PASS")
    print("=" * 60)

    print("M23.1 RELAY PROTOCOL: PASS")
    print("M23.2 RELAY SERVER: PASS")
    print("M23.3 RELAY CLIENT: PASS")
    print("M23.4 DIRECT → RELAY FALLBACK: PASS")
    print("M23.5 RELAY INTEGRATION: PASS")

    print()
    print("HYPERSPACE RELAY / FALLBACK: COMPLETE")

    print("=" * 60)


if __name__ == "__main__":
    main()