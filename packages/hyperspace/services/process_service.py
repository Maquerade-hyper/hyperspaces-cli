from hyperspace.infrastructure.system import SystemDiscovery


class ProcessService:
    def __init__(self):
        self.discovery = SystemDiscovery()

    def list_processes(self):
        return self.discovery.processes()