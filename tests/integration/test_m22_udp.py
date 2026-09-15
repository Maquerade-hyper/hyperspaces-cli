from hyperspace.services.udp_traversal_service import (
    UDPTraversalService,
)


def main() -> None:

    print("=" * 60)
    print("HYPERSPACE M22.2 UDP TRAVERSAL")
    print("=" * 60)

    service = UDPTraversalService(
        host="127.0.0.1",
        port=8766,
    )

    print()
    print("[1] Creating UDP socket...")

    sock = service.bind()

    print("    UDP BIND: PASS")
    print("    ADDRESS:", sock.getsockname())

    print()
    print("[2] Sending local UDP packet...")

    result = service.send(
        host="127.0.0.1",
        port=8766,
    )

    print("    SENT:", result.reachable)

    if result.response:
        print("    RESPONSE:", result.response)

    if result.error:
        print("    ERROR:", result.error)

    sock.close()

    print()
    print("=" * 60)

    if result.reachable:
        print("M22.2 RESULT: PASS")
        print("UDP SOCKET: PASS")
        print("UDP PACKET: PASS")
    else:
        print("M22.2 RESULT: FAILED")

    print("=" * 60)


if __name__ == "__main__":
    main()