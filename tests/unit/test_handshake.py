import json

from hyperspace.core.models import Node
from hyperspace.core.protocols.messages import (
    HandshakeAck,
    NodeHandshake,
)
from hyperspace.services.handshake_service import HandshakeService


def test_node_handshake_serialization():
    handshake = NodeHandshake(
        node_id="node-01",
        hostname="test-pc",
        platform="Windows",
        ip_address="192.168.1.3",
        port=8765,
    )

    data = handshake.model_dump()

    assert data["message_type"] == "node_handshake"
    assert data["node_id"] == "node-01"
    assert data["hostname"] == "test-pc"
    assert data["ip_address"] == "192.168.1.3"
    assert data["port"] == 8765


def test_handshake_ack():
    ack = HandshakeAck(
        status="accepted",
        node_id="node-01",
    )

    assert ack.message_type == "handshake_ack"
    assert ack.status == "accepted"
    assert ack.node_id == "node-01"


def test_handshake_service():
    class FakeTransport:
        def send_json(self, host, port, payload):
            assert host == "192.168.1.4"
            assert port == 8765
            assert payload["message_type"] == "node_handshake"
            assert payload["node_id"] == "node-01"

            return {
                "message_type": "handshake_ack",
                "status": "accepted",
                "node_id": "node-01",
            }

    node = Node(
        node_id="node-01",
        hostname="test-pc",
        platform="Windows",
        ip_address="192.168.1.4",
        port=8765,
    )

    result = HandshakeService(
        transport=FakeTransport()
    ).handshake(node)

    assert result["message_type"] == "handshake_ack"
    assert result["status"] == "accepted"
    assert result["node_id"] == "node-01"