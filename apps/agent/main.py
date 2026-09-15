import threading
import time

from hyperspace.services import (
    DiscoveryService,
    HeartbeatService,
    MeshControllerService,
    NodeIdentityService,
    ResourceService,
)

from hyperspace.services.security_identity_service import (
    SecurityIdentityService,
)

from hyperspace.services.security_integration_service import (
    SecurityIntegrationService,
)

from hyperspace.services.permission_service import (
    Role,
)

from hyperspace.infrastructure.networking.tcp_transport import (
    TCPTransport,
)

from hyperspace.infrastructure.runtime import bootstrap_runtime

def main():
    bootstrap_runtime()

    heartbeat = HeartbeatService(interval=10)

    # =====================================================
    # CORE SERVICES
    # =====================================================

    resource_service = ResourceService()
    discovery_service = DiscoveryService()
    controller = MeshControllerService()
    node_identity = NodeIdentityService()

    # =====================================================
    # NODE IDENTITY
    # =====================================================

    node = node_identity.get_node()

    resources = resource_service.get_resources()

    # =====================================================
    # SECURITY
    # =====================================================

    security_identity = SecurityIdentityService()
    security = SecurityIntegrationService()

    identity = security_identity.get_identity()

    # -----------------------------------------------------
    # Trust the local controller identity.
    #
    # During the current single-PC development phase,
    # controller and agent are running on the same machine.
    #
    # The controller therefore presents this identity when
    # sending execution requests to the local worker.
    # -----------------------------------------------------

    security.register_node(
        identity,
        Role.CONTROLLER,
    )

    # =====================================================
    # MESH
    # =====================================================

    mesh = controller.get_mesh()

    if mesh is None:
        print("Hyperspace Agent cannot start.")
        print("No mesh exists on this controller.")
        return

    # =====================================================
    # TCP TRANSPORT
    # =====================================================

    tcp_transport = TCPTransport(
        host="::",
        port=node.port,
        security=security,
    )

    # =====================================================
    # TCP SERVER
    # =====================================================

    server_thread = threading.Thread(
        target=tcp_transport.start_server,
        daemon=True,
    )

    server_thread.start()

    # =====================================================
    # HEARTBEAT
    # =====================================================

    heartbeat = HeartbeatService()
    heartbeat.start()

    # =====================================================
    # STARTUP INFORMATION
    # =====================================================

    print()
    print("Hyperspace Agent started")
    print("------------------------")
    print(f"Node ID: {node.node_id}")
    print(f"Network: {node.ip_address}:{node.port}")
    print(f"Mesh:    {mesh.name}")
    print(f"Mesh ID: {mesh.mesh_id}")
    print(f"Security fingerprint: {identity.fingerprint}")
    print()

    # =====================================================
    # DISCOVERY LOOP
    # =====================================================

    last_discovery = 0

    while True:

        current_time = time.time()

        if current_time - last_discovery >= 5:

            try:

                message = discovery_service.announce_controller(
                    mesh_id=mesh.mesh_id,
                    tcp_port=node.port,
                )

                print(
                    f"LAN Discovery: controller advertised "
                    f"at {message['ip_address']}:{message['port']}"
                )

            except Exception as exc:

                print(
                    f"LAN Discovery error: {exc}"
                )

            last_discovery = current_time

        # =================================================
        # RESOURCE STATUS
        # =================================================

        print(
            f"Node: online | "
            f"Resources: {resources.model_dump()}"
        )

        time.sleep(5)


if __name__ == "__main__":
    main()