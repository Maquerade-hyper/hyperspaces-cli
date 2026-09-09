from hyperspace.infrastructure.system import SystemDiscovery


def test_cpu_discovery():
    cpu = SystemDiscovery().cpu()

    assert cpu["cores"] > 0
    assert cpu["threads"] >= cpu["cores"]
    assert 0 <= cpu["utilization_percent"] <= 100


def test_memory_discovery():
    memory = SystemDiscovery().memory()

    assert memory["total_gb"] > 0
    assert memory["available_gb"] >= 0
    assert 0 <= memory["utilization_percent"] <= 100


def test_process_discovery():
    processes = SystemDiscovery().processes()

    assert isinstance(processes, list)
    assert len(processes) > 0