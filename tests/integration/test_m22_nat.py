from hyperspace.services.nat_detection_service import (
    NATDetectionService,
)


def main() -> None:

    print("=" * 60)
    print("HYPERSPACE M22.1 NAT DETECTION")
    print("=" * 60)

    service = NATDetectionService()

    result = service.detect()

    print()
    print("HOSTNAME:")
    print(" ", result.hostname)

    print()
    print("LOCAL ADDRESSES:")
    for address in result.local_addresses:
        print(" ", address)

    print()
    print("IPv4:")
    for address in result.ipv4_addresses:
        print(" ", address)

    print()
    print("IPv6:")
    for address in result.ipv6_addresses:
        print(" ", address)

    print()
    print("HAS IPv4:", result.has_ipv4)
    print("HAS IPv6:", result.has_ipv6)

    print()
    print("=" * 60)

    if result.has_ipv4 or result.has_ipv6:
        print("M22.1 RESULT: PASS")
    else:
        print("M22.1 RESULT: FAILED")

    print("=" * 60)


if __name__ == "__main__":
    main()