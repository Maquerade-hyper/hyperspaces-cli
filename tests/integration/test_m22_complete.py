from __future__ import annotations

import socket
import threading

from hyperspace.services.nat_detection_service import (
    NATDetectionService,
)

from hyperspace.services.nat_traversal_service import (
    CandidateExchangeService,
    NATTraversalService,
    UDPHolePunchService,
)


def run_udp_peer(
    port_holder: list[int],
    ready: threading.Event,
    stop: threading.Event,
) -> None:

    sock = socket.socket(
        socket.AF_INET,
        socket.SOCK_DGRAM,
    )

    sock.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_REUSEADDR,
        1,
    )

    sock.bind(
        ("127.0.0.1", 0)
    )

    port_holder.append(
        sock.getsockname()[1]
    )

    sock.settimeout(0.5)

    ready.set()

    try:

        while not stop.is_set():

            try:

                data, address = sock.recvfrom(
                    4096
                )

            except socket.timeout:
                continue

            message = data.decode(
                "utf-8",
                errors="replace",
            )

            if (
                message
                == UDPHolePunchService.MAGIC
            ):

                sock.sendto(
                    UDPHolePunchService.MAGIC.encode(
                        "utf-8"
                    ),
                    address,
                )

    finally:
        sock.close()


def main() -> None:

    print("=" * 60)
    print("HYPERSPACE M22 NAT TRAVERSAL")
    print("=" * 60)

    # =====================================================
    # M22.1
    # =====================================================

    print()
    print("[M22.1] NAT detection...")

    detection = (
        NATDetectionService().detect()
    )

    print("    HOST:", detection.hostname)
    print(
        "    IPv4:",
        detection.ipv4_addresses,
    )
    print(
        "    IPv6:",
        detection.ipv6_addresses,
    )

    if not (
        detection.has_ipv4
        or detection.has_ipv6
    ):
        raise RuntimeError(
            "No network addresses detected."
        )

    print("    NAT DETECTION: PASS")

    # =====================================================
    # M22.2
    # =====================================================

    print()
    print("[M22.2] UDP traversal service...")

    hole_punch = UDPHolePunchService()

    print("    UDP SERVICE: PASS")

    # =====================================================
    # M22.3
    # =====================================================

    print()
    print("[M22.3] Candidate exchange...")

    candidate_service = (
        CandidateExchangeService()
    )

    local_candidates = []

    for address in detection.ipv4_addresses:

        if address.startswith("127."):
            continue

        local_candidates.append(
            candidate_service.create_candidate(
                host=address,
                port=8766,
                address_family="ipv4",
            )
        )

    local_candidates.append(
        candidate_service.create_candidate(
            host="127.0.0.1",
            port=8766,
            address_family="ipv4",
        )
    )

    for candidate in local_candidates:
        print(
            "    CANDIDATE:",
            candidate.endpoint,
        )

    exchange = (
        candidate_service.create_exchange(
            node_id="m22-node-a",
            candidates=local_candidates,
        )
    )

    serialized = (
        candidate_service.serialize(
            exchange
        )
    )

    restored = (
        candidate_service.deserialize(
            serialized
        )
    )

    if restored.node_id != "m22-node-a":
        raise RuntimeError(
            "Candidate node ID mismatch."
        )

    if len(restored.candidates) != len(
        local_candidates
    ):
        raise RuntimeError(
            "Candidate count mismatch."
        )

    print("    SERIALIZATION: PASS")
    print("    DESERIALIZATION: PASS")
    print("    CANDIDATE EXCHANGE: PASS")

    # =====================================================
    # M22.4
    # =====================================================

    print()
    print("[M22.4] UDP hole punching...")

    peer_port: list[int] = []
    peer_ready = threading.Event()
    peer_stop = threading.Event()

    peer_thread = threading.Thread(
        target=run_udp_peer,
        args=(
            peer_port,
            peer_ready,
            peer_stop,
        ),
        daemon=True,
    )

    peer_thread.start()

    if not peer_ready.wait(
        timeout=3
    ):
        raise RuntimeError(
            "UDP peer failed to start."
        )

    remote_port = peer_port[0]

    print(
        "    REMOTE UDP PORT:",
        remote_port,
    )

    punch_result = hole_punch.punch(
        remote_host="127.0.0.1",
        remote_port=remote_port,
        local_host="127.0.0.1",
        local_port=0,
        attempts=5,
        interval=0.2,
        timeout=3,
    )

    print(
        "    LOCAL UDP PORT:",
        punch_result.local_port,
    )

    print(
        "    PACKETS SENT:",
        punch_result.packets_sent,
    )

    print(
        "    CONNECTED:",
        punch_result.connected,
    )

    if punch_result.error:
        print(
            "    ERROR:",
            punch_result.error,
        )

    if not punch_result.connected:
        peer_stop.set()
        raise RuntimeError(
            "UDP hole punching failed."
        )

    print("    UDP HOLE PUNCH: PASS")

    # =====================================================
    # M22.5
    # =====================================================

    print()
    print("[M22.5] Complete NAT traversal engine...")

    remote_candidate = (
        candidate_service.create_candidate(
            host="127.0.0.1",
            port=remote_port,
            address_family="ipv4",
        )
    )

    local_candidate = (
        candidate_service.create_candidate(
            host="127.0.0.1",
            port=0,
            address_family="ipv4",
        )
    )

    traversal = NATTraversalService(
        candidate_exchange=candidate_service,
        hole_punch=hole_punch,
    )

    traversal_result = (
        traversal.traverse(
            node_id="m22-node-a",
            local_candidates=[
                local_candidate,
            ],
            remote_candidates=[
                remote_candidate,
            ],
        )
    )

    print(
        "    TRAVERSAL CONNECTED:",
        traversal_result.connected,
    )

    if traversal_result.selected_candidate:
        print(
            "    SELECTED CANDIDATE:",
            traversal_result.selected_candidate.endpoint,
        )

    if traversal_result.error:
        print(
            "    ERROR:",
            traversal_result.error,
        )

    if not traversal_result.connected:
        peer_stop.set()
        raise RuntimeError(
            "Complete NAT traversal failed."
        )

    print("    TRAVERSAL ENGINE: PASS")

    peer_stop.set()
    peer_thread.join(
        timeout=1
    )

    # =====================================================
    # FINAL
    # =====================================================

    print()
    print("=" * 60)
    print("M22 RESULT: PASS")
    print("=" * 60)

    print("M22.1 NAT DETECTION: PASS")
    print("M22.2 UDP TRAVERSAL: PASS")
    print("M22.3 CANDIDATE EXCHANGE: PASS")
    print("M22.4 UDP HOLE PUNCHING: PASS")
    print("M22.5 NAT TRAVERSAL ENGINE: PASS")

    print()
    print(
        "HYPERSPACE NAT TRAVERSAL FOUNDATION: COMPLETE"
    )

    print("=" * 60)


if __name__ == "__main__":
    main()