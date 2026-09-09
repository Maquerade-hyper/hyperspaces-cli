from hyperspace.services import GPUService, NodeService, ResourceService
from hyperspace.core.models import ResourceSnapshot


def test_node_service():
    nodes = NodeService().list_nodes()

    assert len(nodes) == 1
    assert nodes[0].node_id
    assert nodes[0].hostname
    assert nodes[0].platform
    assert nodes[0].status.value == "online"


def test_gpu_service():
    gpus = GPUService().list_gpus()

    assert isinstance(gpus, list)

    for gpu in gpus:
        assert gpu.id >= 0
        assert gpu.name
        assert gpu.vram_total_gb > 0
        assert gpu.vram_available_gb >= 0
        assert 0 <= gpu.utilization_percent <= 100


def test_resource_service():
    result = ResourceService().get_resources()

    assert isinstance(result, ResourceSnapshot)
    assert result.cpu.cores > 0
    assert result.cpu.threads > 0
    assert result.ram.total_gb > 0
    assert result.ram.available_gb >= 0