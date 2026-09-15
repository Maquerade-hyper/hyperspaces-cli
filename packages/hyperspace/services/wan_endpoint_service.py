from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass
class WANEndpoint:
    host: str
    port: int = 8765
    scheme: str = "tcp"

    @property
    def address(self) -> str:
        if ":" in self.host and not (
            self.host.startswith("[")
            and self.host.endswith("]")
        ):
            return f"[{self.host}]:{self.port}"

        return f"{self.host}:{self.port}"

    @property
    def url(self) -> str:
        if ":" in self.host and not (
            self.host.startswith("[")
            and self.host.endswith("]")
        ):
            return f"{self.scheme}://[{self.host}]:{self.port}"

        return f"{self.scheme}://{self.host}:{self.port}"


class WANEndpointService:
    """
    Creates and validates explicit WAN endpoints.

    M21 introduces explicit Internet addressing while leaving
    the existing LAN discovery system unchanged.
    """

    DEFAULT_PORT = 8765

    def create(
        self,
        host: str,
        port: int = DEFAULT_PORT,
    ) -> WANEndpoint:
        host = host.strip()

        if not host:
            raise ValueError(
                "WAN endpoint host cannot be empty."
            )

        if port < 1 or port > 65535:
            raise ValueError(
                "WAN endpoint port must be between 1 and 65535."
            )

        return WANEndpoint(
            host=host,
            port=port,
        )

    def parse(
        self,
        endpoint: str,
    ) -> WANEndpoint:
        endpoint = endpoint.strip()

        if not endpoint:
            raise ValueError(
                "WAN endpoint cannot be empty."
            )

        if "://" not in endpoint:
            endpoint = f"tcp://{endpoint}"

        parsed = urlparse(endpoint)

        if not parsed.hostname:
            raise ValueError(
                "Invalid WAN endpoint host."
            )

        port = (
            parsed.port
            if parsed.port is not None
            else self.DEFAULT_PORT
        )

        return self.create(
            host=parsed.hostname,
            port=port,
        )

    def validate(
        self,
        endpoint: WANEndpoint,
    ) -> bool:
        if not endpoint.host:
            return False

        if endpoint.port < 1:
            return False

        if endpoint.port > 65535:
            return False

        return endpoint.scheme == "tcp"


def create_wan_endpoint(
    host: str,
    port: int = WANEndpointService.DEFAULT_PORT,
) -> WANEndpoint:
    return WANEndpointService().create(
        host=host,
        port=port,
    )


def parse_wan_endpoint(
    endpoint: str,
) -> WANEndpoint:
    return WANEndpointService().parse(
        endpoint
    )