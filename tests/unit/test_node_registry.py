from hyperspace.core.models import Node, NodeStatus
from hyperspace.services import NodeRegistryService


def make_node(node_id: str) -> Node:
    return Node(
        node_id=node_id,
        hostname=f"pc-{node_id}",
        platform="Windows",
        ip_address="192.168.1.10",
        port=8765,
        status=NodeStatus.ONLINE,
    )


def test_register_node():
    registry = NodeRegistryService()

    node = make_node("node-01")

    result = registry.register(node)

    assert result == node
    assert registry.get("node-01") == node


def test_list_nodes():
    registry = NodeRegistryService()

    node1 = make_node("node-01")
    node2 = make_node("node-02")

    registry.register(node1)
    registry.register(node2)

    nodes = registry.list_nodes()

    assert len(nodes) == 2
    assert node1 in nodes
    assert node2 in nodes


def test_last_seen():
    registry = NodeRegistryService()

    registry.register(make_node("node-01"))

    timestamp = registry.last_seen("node-01")

    assert timestamp is not None


def test_remove_node():
    registry = NodeRegistryService()

    registry.register(make_node("node-01"))

    registry.remove("node-01")

    assert registry.get("node-01") is None
    assert registry.last_seen("node-01") is None


def test_clear_registry():
    registry = NodeRegistryService()

    registry.register(make_node("node-01"))
    registry.register(make_node("node-02"))

    registry.clear()

    assert registry.list_nodes() == []