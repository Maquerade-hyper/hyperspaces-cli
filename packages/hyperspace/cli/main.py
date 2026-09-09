import threading
import time

from hyperspace.infrastructure.networking.tcp_transport import TCPTransport

from hyperspace.services import (
    HeartbeatService,
    NodeService,
    ResourceService,
    DiscoveryService,
)

from hyperspace.infrastructure.runtime import bootstrap_runtime


def main():
    # Initialize Hyperspace runtime directories and configuration
    bootstrap_runtime()

    heartbeat = HeartbeatService(interval=10)
    node_service = NodeService(heartbeat=heartbeat)
    resource_service = ResourceService()
    discovery_service = DiscoveryService()

    network = TCPTransport()

    def discovery_loop():
        while True:
            try:
                discovery_service.announce()
                print("UDP Discovery: broadcast sent")
                time.sleep(10)

            except Exception as exc:
                print(f"Discovery error: {exc}")
                time.sleep(10)

    def discovery_listener():
        try:
            local_node = node_service.get_local_node()

            def handle_discovery(message, address):
                if message.get("node_id") == local_node.node_id:
                    return

                try:
                    node = discovery_service.process_discovery(
                        message,
                        address,
                    )

                    if node is not None:
                        print(
                            f"Remote node registered: "
                            f"{node.hostname} "
                            f"({node.ip_address}:{node.port})"
                        )

                except Exception as exc:
                    print(f"Discovery processing error: {exc}")

            discovery_service.listen(handle_discovery)

        except Exception as exc:
            print(f"Discovery listener error: {exc}")

    server_thread = threading.Thread(
        target=network.start_server,
        daemon=True,
    )
    server_thread.start()

    discovery_thread = threading.Thread(
        target=discovery_loop,
        daemon=True,
    )
    discovery_thread.start()

    discovery_listener_thread = threading.Thread(
        target=discovery_listener,
        daemon=True,
    )
    discovery_listener_thread.start()

    heartbeat.start()

    node = node_service.get_local_node()

    print("Hyperspace Agent started")
    print(f"Node ID: {node.node_id}")
    print(f"Hostname: {node.hostname}")
    print(f"Network: {node.ip_address}:{node.port}")
    print("TCP Server: active")
    print("UDP Discovery: active")
    print("UDP Discovery Listener: active")

    try:
        while True:
            node = node_service.get_local_node()
            resources = resource_service.get_resources()

            print(
                f"Node: {node.status.value} | "
                f"CPU: {resources.cpu.utilization_percent:.1f}% | "
                f"RAM: {resources.ram.utilization_percent:.1f}% | "
                f"GPUs: {len(resources.gpus)}"
            )

            time.sleep(5)

    except KeyboardInterrupt:
        heartbeat.stop()
        print("\nHyperspace Agent stopped.")


if __name__ == "__main__":
    main()