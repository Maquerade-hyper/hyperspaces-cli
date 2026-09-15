from __future__ import annotations

import socket
from dataclasses import dataclass


@dataclass
class NATDetectionResult:
    hostname: str
    local_addresses: list[str]
    ipv4_addresses: list[str]
    ipv6_addresses: list[str]
    has_ipv4: bool
    has_ipv6: bool


class NATDetectionService:
    """
    Detects the network addresses available to a Hyperspace node.

    This is the first NAT-traversal foundation.

    It does not:
    - modify router configuration
    - require port forwarding
    - depend on an ISP
    - perform hole punching
    - provide relay functionality
    """

    def detect(self) -> NATDetectionResult:
        hostname = socket.gethostname()

        local_addresses: set[str] = set()
        ipv4_addresses: set[str] = set()
        ipv6_addresses: set[str] = set()

        try:
            addr_info = socket.getaddrinfo(
                hostname,
                None,
                socket.AF_UNSPEC,
                socket.SOCK_STREAM,
            )

            for info in addr_info:
                family = info[0]
                address = info[4][0]

                if not address:
                    continue

                local_addresses.add(address)

                if family == socket.AF_INET:
                    ipv4_addresses.add(address)

                elif family == socket.AF_INET6:
                    ipv6_addresses.add(address)

        except socket.gaierror:
            pass

        return NATDetectionResult(
            hostname=hostname,
            local_addresses=sorted(local_addresses),
            ipv4_addresses=sorted(ipv4_addresses),
            ipv6_addresses=sorted(ipv6_addresses),
            has_ipv4=bool(ipv4_addresses),
            has_ipv6=bool(ipv6_addresses),
        )


def detect_nat_network() -> NATDetectionResult:
    return NATDetectionService().detect()