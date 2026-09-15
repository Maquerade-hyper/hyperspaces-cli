from __future__ import annotations

from hyperspace.services.security_identity_service import (
    SecurityIdentityService,
)
from hyperspace.services.wan_coordinator_service import (
    WANCoordinatorService,
)
from hyperspace.services.wan_connection_manager_service import (
    WANConnectionManagerService,
)
from hyperspace.services.wan_connection_service import (
    WANConnectionService,
)


def main() -> None:

    print("=" * 60)
    print("HYPERSPACE M21.5 WAN END-TO-END TEST")
    print("=" * 60)

    # ---------------------------------------------------------
    # 1. LOAD EXISTING HYPERSPACE IDENTITY
    # ---------------------------------------------------------

    print()
    print("[1] Loading existing Hyperspace identity...")

    identity = SecurityIdentityService().get_identity()

    print("    NODE ID:", identity.node_id)
    print("    FINGERPRINT:", identity.fingerprint)
    print("    IDENTITY: PASS")

    # ---------------------------------------------------------
    # 2. REGISTER WAN ENDPOINT
    # ---------------------------------------------------------

    print()
    print("[2] Registering WAN endpoint...")

    coordinator = WANCoordinatorService()

    coordinator.register(
        node_id=identity.node_id,
        mesh_id="m21-test-mesh",
        endpoints=[
            "127.0.0.1:8765",
        ],
        protocols=[
            "tcp",
        ],
    )

    print("    COORDINATOR: PASS")

    # ---------------------------------------------------------
    # 3. DISCOVER NODE
    # ---------------------------------------------------------

    print()
    print("[3] Discovering node through WAN coordinator...")

    manager = WANConnectionManagerService(
        coordinator=coordinator,
    )

    node = manager.discover(
        node_id=identity.node_id,
        mesh_id="m21-test-mesh",
    )

    if node is None:
        raise RuntimeError(
            "M21.5 WAN discovery failed."
        )

    print("    DISCOVERY: PASS")
    print("    NODE:", node.node_id)
    print("    ENDPOINTS:", node.endpoints)

    # ---------------------------------------------------------
    # 4. CONNECT USING EXISTING TCP TRANSPORT
    # ---------------------------------------------------------

    print()
    print("[4] Connecting to WAN endpoint...")

    endpoint = manager.endpoint_service.parse(
        node.endpoints[0]
    )

    connection = WANConnectionService().connect_endpoint(
        endpoint,
        payload={
            "message_type": "node_handshake",
            "node_id": identity.node_id,
            "fingerprint": identity.fingerprint,
        },
    )

    print("    CONNECTED:", connection.connected)

    if connection.error:
        print("    ERROR:", connection.error)

    if connection.response:
        print("    RESPONSE:", connection.response)

    # ---------------------------------------------------------
    # 5. VALIDATE EXISTING HYPERSPACE HANDSHAKE
    # ---------------------------------------------------------

    print()
    print("[5] Validating authenticated Hyperspace handshake...")

    if not connection.connected:
        print()
        print("=" * 60)
        print("M21.5 RESULT: FAILED")
        print("TCP CONNECTION: FAILED")
        print("=" * 60)
        return

    response = connection.response or {}

    authenticated = (
        response.get("authenticated") is True
    )

    accepted = (
        response.get("status") == "accepted"
        and authenticated
    )

    print("    STATUS:", response.get("status"))
    print("    AUTHENTICATED:", authenticated)
    print("    ACCEPTED:", accepted)

    # ---------------------------------------------------------
    # FINAL RESULT
    # ---------------------------------------------------------

    print()
    print("=" * 60)

    if accepted:
        print("M21.5 RESULT: PASS")
        print("WAN ENDPOINT: PASS")
        print("WAN TCP CONNECTION: PASS")
        print("HYPERSPACE AUTHENTICATION: PASS")
        print("HYPERSPACE HANDSHAKE: PASS")
        print("M21: COMPLETE")
    else:
        print("M21.5 RESULT: FAILED")
        print(
            "ERROR:",
            response.get("error")
            or response.get("reason")
            or "Handshake was not accepted.",
        )

    print("=" * 60)


if __name__ == "__main__":
    main()