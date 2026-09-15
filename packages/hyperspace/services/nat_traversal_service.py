from __future__ import annotations

import json
import socket
import time
from dataclasses import asdict, dataclass


# =========================================================
# NETWORK CANDIDATE
# =========================================================

@dataclass
class NetworkCandidate:
    host: str
    port: int
    protocol: str = "udp"
    address_family: str = "ipv4"

    @property
    def endpoint(self) -> str:
        if self.address_family == "ipv6":
            return f"[{self.host}]:{self.port}"

        return f"{self.host}:{self.port}"


# =========================================================
# CANDIDATE EXCHANGE
# =========================================================

@dataclass
class CandidateExchangeResult:
    node_id: str
    candidates: list[NetworkCandidate]

    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id,
            "candidates": [
                asdict(candidate)
                for candidate in self.candidates
            ],
        }

    def serialize(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def deserialize(
        cls,
        payload: str,
    ) -> "CandidateExchangeResult":

        data = json.loads(payload)

        candidates = [
            NetworkCandidate(
                host=item["host"],
                port=int(item["port"]),
                protocol=item.get(
                    "protocol",
                    "udp",
                ),
                address_family=item.get(
                    "address_family",
                    "ipv4",
                ),
            )
            for item in data.get(
                "candidates",
                [],
            )
        ]

        return cls(
            node_id=data["node_id"],
            candidates=candidates,
        )


class CandidateExchangeService:

    def create_candidate(
        self,
        host: str,
        port: int,
        address_family: str = "ipv4",
    ) -> NetworkCandidate:

        if not host:
            raise ValueError(
                "Candidate host cannot be empty."
            )

        # Port 0 is allowed for a LOCAL ephemeral socket.
        # Advertised/remote candidates must use a real port.
        if port < 0 or port > 65535:
            raise ValueError(
                "Candidate port must be between 0 and 65535."
            )

        if address_family not in {
            "ipv4",
            "ipv6",
        }:
            raise ValueError(
                "Unsupported address family."
            )

        return NetworkCandidate(
            host=host,
            port=port,
            protocol="udp",
            address_family=address_family,
        )

    def create_exchange(
        self,
        node_id: str,
        candidates: list[NetworkCandidate],
    ) -> CandidateExchangeResult:

        if not node_id:
            raise ValueError(
                "node_id cannot be empty."
            )

        if not candidates:
            raise ValueError(
                "At least one network candidate is required."
            )

        for candidate in candidates:
            if candidate.port == 0:
                raise ValueError(
                    "Cannot advertise an ephemeral port."
                )

        return CandidateExchangeResult(
            node_id=node_id,
            candidates=candidates,
        )

    def serialize(
        self,
        exchange: CandidateExchangeResult,
    ) -> str:

        return exchange.serialize()

    def deserialize(
        self,
        payload: str,
    ) -> CandidateExchangeResult:

        return CandidateExchangeResult.deserialize(
            payload
        )


# =========================================================
# HOLE PUNCH RESULT
# =========================================================

@dataclass
class HolePunchResult:
    local_host: str
    local_port: int
    remote_host: str
    remote_port: int
    attempts: int
    packets_sent: int
    connected: bool
    response: str | None = None
    error: str | None = None


# =========================================================
# UDP HOLE PUNCHING
# =========================================================

class UDPHolePunchService:

    MAGIC = "HYPERSPACE_HOLE_PUNCH"

    def create_socket(
        self,
        address_family: int = socket.AF_INET,
    ) -> socket.socket:

        sock = socket.socket(
            address_family,
            socket.SOCK_DGRAM,
        )

        sock.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1,
        )

        sock.settimeout(0.5)

        return sock

    def punch(
        self,
        remote_host: str,
        remote_port: int,
        local_host: str = "0.0.0.0",
        local_port: int = 0,
        attempts: int = 5,
        interval: float = 0.2,
        timeout: float = 3.0,
    ) -> HolePunchResult:

        if not remote_host:
            return HolePunchResult(
                local_host=local_host,
                local_port=local_port,
                remote_host=remote_host,
                remote_port=remote_port,
                attempts=0,
                packets_sent=0,
                connected=False,
                error="Remote host cannot be empty.",
            )

        if remote_port < 1 or remote_port > 65535:
            return HolePunchResult(
                local_host=local_host,
                local_port=local_port,
                remote_host=remote_host,
                remote_port=remote_port,
                attempts=0,
                packets_sent=0,
                connected=False,
                error="Invalid remote UDP port.",
            )

        address_family = (
            socket.AF_INET6
            if ":" in remote_host
            else socket.AF_INET
        )

        sock = self.create_socket(
            address_family=address_family
        )

        packets_sent = 0

        try:

            sock.bind(
                (
                    local_host,
                    local_port,
                )
            )

            actual_local_port = sock.getsockname()[1]

            payload = self.MAGIC.encode(
                "utf-8"
            )

            start_time = time.monotonic()

            for attempt in range(
                1,
                attempts + 1,
            ):

                try:

                    if address_family == socket.AF_INET6:

                        sock.sendto(
                            payload,
                            (
                                remote_host,
                                remote_port,
                                0,
                                0,
                            ),
                        )

                    else:

                        sock.sendto(
                            payload,
                            (
                                remote_host,
                                remote_port,
                            ),
                        )

                    packets_sent += 1

                except OSError:
                    pass

                deadline = (
                    time.monotonic()
                    + interval
                )

                while time.monotonic() < deadline:

                    if (
                        time.monotonic()
                        - start_time
                        > timeout
                    ):
                        break

                    try:

                        data, _address = (
                            sock.recvfrom(
                                4096
                            )
                        )

                        message = data.decode(
                            "utf-8",
                            errors="replace",
                        )

                        if (
                            message
                            == self.MAGIC
                        ):

                            return HolePunchResult(
                                local_host=local_host,
                                local_port=actual_local_port,
                                remote_host=remote_host,
                                remote_port=remote_port,
                                attempts=attempt,
                                packets_sent=packets_sent,
                                connected=True,
                                response=message,
                            )

                    except socket.timeout:
                        continue

            return HolePunchResult(
                local_host=local_host,
                local_port=actual_local_port,
                remote_host=remote_host,
                remote_port=remote_port,
                attempts=attempts,
                packets_sent=packets_sent,
                connected=False,
                error=(
                    "UDP hole punching did not "
                    "receive a peer response."
                ),
            )

        except Exception as exc:

            return HolePunchResult(
                local_host=local_host,
                local_port=local_port,
                remote_host=remote_host,
                remote_port=remote_port,
                attempts=attempts,
                packets_sent=packets_sent,
                connected=False,
                error=str(exc),
            )

        finally:
            sock.close()


# =========================================================
# NAT TRAVERSAL RESULT
# =========================================================

@dataclass
class NATTraversalResult:
    node_id: str
    local_candidates: list[NetworkCandidate]
    remote_candidates: list[NetworkCandidate]
    connected: bool
    selected_candidate: NetworkCandidate | None = None
    error: str | None = None


# =========================================================
# NAT TRAVERSAL COORDINATOR
# =========================================================

class NATTraversalService:

    def __init__(
        self,
        candidate_exchange: CandidateExchangeService | None = None,
        hole_punch: UDPHolePunchService | None = None,
    ):

        self.candidate_exchange = (
            candidate_exchange
            or CandidateExchangeService()
        )

        self.hole_punch = (
            hole_punch
            or UDPHolePunchService()
        )

    def exchange_candidates(
        self,
        node_id: str,
        candidates: list[NetworkCandidate],
    ) -> str:

        exchange = (
            self.candidate_exchange.create_exchange(
                node_id=node_id,
                candidates=candidates,
            )
        )

        return self.candidate_exchange.serialize(
            exchange
        )

    def parse_candidates(
        self,
        payload: str,
    ) -> CandidateExchangeResult:

        return self.candidate_exchange.deserialize(
            payload
        )

    def traverse(
        self,
        node_id: str,
        local_candidates: list[NetworkCandidate],
        remote_candidates: list[NetworkCandidate],
    ) -> NATTraversalResult:

        if not local_candidates:
            return NATTraversalResult(
                node_id=node_id,
                local_candidates=[],
                remote_candidates=remote_candidates,
                connected=False,
                error="No local candidates available.",
            )

        if not remote_candidates:
            return NATTraversalResult(
                node_id=node_id,
                local_candidates=local_candidates,
                remote_candidates=[],
                connected=False,
                error="No remote candidates available.",
            )

        errors = []

        for remote in remote_candidates:

            if remote.protocol != "udp":
                continue

            for local in local_candidates:

                if local.protocol != "udp":
                    continue

                try:

                    result = (
                        self.hole_punch.punch(
                            remote_host=remote.host,
                            remote_port=remote.port,
                            local_host=local.host,
                            local_port=local.port,
                        )
                    )

                    if result.connected:

                        return NATTraversalResult(
                            node_id=node_id,
                            local_candidates=local_candidates,
                            remote_candidates=remote_candidates,
                            connected=True,
                            selected_candidate=remote,
                        )

                    if result.error:
                        errors.append(
                            f"{remote.endpoint}: "
                            f"{result.error}"
                        )

                except Exception as exc:

                    errors.append(
                        f"{remote.endpoint}: {exc}"
                    )

        return NATTraversalResult(
            node_id=node_id,
            local_candidates=local_candidates,
            remote_candidates=remote_candidates,
            connected=False,
            error="; ".join(errors)
            if errors
            else "No compatible UDP candidates.",
        )


# =========================================================
# HELPER
# =========================================================

def create_network_candidate(
    host: str,
    port: int,
    address_family: str = "ipv4",
) -> NetworkCandidate:

    return CandidateExchangeService().create_candidate(
        host=host,
        port=port,
        address_family=address_family,
    )