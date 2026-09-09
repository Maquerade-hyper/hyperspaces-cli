from hyperspace.core.models import CPU, GPU, Node, NodeStatus, RAM, ResourceSnapshot


def test_cpu():
    cpu = CPU(cores=8, threads=16)
    assert cpu.cores == 8
    assert cpu.threads == 16


def test_ram():
    ram = RAM(total_gb=32, available_gb=20)
    assert ram.total_gb == 32


def test_gpu():
    gpu = GPU(
        id=0,
        name="Test GPU",
        vram_total_gb=8,
        vram_available_gb=6,
    )
    assert gpu.vram_total_gb == 8


def test_node():
    node = Node(
        node_id="node-01",
        hostname="test-pc",
        platform="Windows",
    )

    assert node.status == NodeStatus.UNKNOWN
    assert node.platform == "Windows"


def test_resource_snapshot():
    snapshot = ResourceSnapshot(
        cpu=CPU(cores=8, threads=16),
        ram=RAM(total_gb=32, available_gb=20),
    )
    assert snapshot.cpu.cores == 8