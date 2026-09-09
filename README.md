# Hyperspace

Hyperspace is a distributed compute mesh designed to combine the CPU, RAM,
and GPU resources of multiple computers into a shared compute environment.

The long-term goal is to make distributed AI workloads executable across
multiple connected machines through a unified resource pool, scheduler,
and execution system.

## Current Status

Hyperspace is currently in the core backend and distribution stage.

Implemented subsystems include:

- Node identity and resource detection
- LAN node discovery
- TCP communication
- Mesh creation and joining
- Membership and authorization
- Shared CPU/RAM/GPU resource management
- Resource allocation
- Job definition and tracking
- Persistent job queue
- Job scheduling
- Remote execution
- Result and artifact storage
- Fault detection and retry
- Distributed execution foundation
- GPU registry and allocation
- Mutual TLS transport security
- Controller API
- Dashboard
- CLI
- Runtime bootstrap
- Installation management
- Environment validation
- Git-based distribution foundation

## Architecture

```text
                    Hyperspace Controller
                            |
              +-------------+-------------+
              |             |             |
           Node A        Node B        Node C
              |             |             |
           CPU/RAM/GPU   CPU/RAM/GPU   CPU/RAM/GPU
              \             |             /
               +------------+------------+
                            |
                     Resource Pool
                            |
                        Scheduler
                            |
                          Jobs
                            |
                    Remote Execution
                            |
                    Results / Artifacts