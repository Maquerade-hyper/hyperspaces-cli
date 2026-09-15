import argparse
import os

import requests

from hyperspace.services import (
    DiscoveryService,
    MeshControllerService,
    MeshInviteService,
    MeshMembershipService,
    NodeIdentityService,
    resolve_join_controller,
)

from hyperspace.infrastructure.networking.tcp_transport import (
    TCPTransport,
)

from hyperspace.infrastructure.runtime import bootstrap_runtime

from hyperspace.services.bootstrap_state_service import (
    BootstrapStateService,
)

from hyperspace.services.bootstrap_state_service import (
    BootstrapStateService,
)


VERSION = "0.1.0"

DEFAULT_CONTROLLER_API = os.environ.get(
    "HYPERSPACE_CONTROLLER",
    "http://localhost:8000",
)

CONTROLLER_API = DEFAULT_CONTROLLER_API


# ============================================================
# CONTROLLER API HELPERS
# ============================================================

def controller_get(path: str):
    response = requests.get(
        f"{CONTROLLER_API}{path}",
        timeout=10,
    )

    response.raise_for_status()

    return response.json()


def controller_post(
    path: str,
    payload=None,
):
    response = requests.post(
        f"{CONTROLLER_API}{path}",
        json=payload,
        timeout=30,
    )

    response.raise_for_status()

    return response.json()


def print_http_error(
    operation: str,
    exc: requests.HTTPError,
):
    print(
        f"{operation} failed: {exc}"
    )

    if exc.response is not None:
        try:
            data = exc.response.json()

            detail = data.get("detail")

            if detail:
                print(
                    f"Reason: {detail}"
                )

        except Exception:
            pass


# ============================================================
# MESH
# ============================================================

def mesh_create(name: str):
    controller = MeshControllerService()

    try:
        mesh = controller.create_mesh(name)

        print("Hyperspace Mesh Created")
        print("-----------------------")
        print(
            f"Name:    {mesh.name}"
        )
        print(
            f"Mesh ID: {mesh.mesh_id}"
        )
        print(
            f"Owner:   {mesh.owner_node_id}"
        )
        print(
            f"Status:  {mesh.status.value}"
        )

    except ValueError as exc:
        print(
            f"Error: {exc}"
        )


def mesh_status():
    controller = MeshControllerService()

    status = controller.status()

    print("Hyperspace Mesh")
    print("----------------")

    if not status["mesh_exists"]:
        print(
            "Status: No mesh created"
        )
        return

    print(
        f"Name:    {status['name']}"
    )
    print(
        f"Mesh ID: {status['mesh_id']}"
    )
    print(
        f"Owner:   {status['owner_node_id']}"
    )
    print(
        f"Status:  {status['status']}"
    )


def mesh_invite():
    controller = MeshControllerService()

    invites = MeshInviteService(
        controller=controller
    )

    try:
        invite = invites.create_invite()

        print(
            "Hyperspace Mesh Invitation"
        )
        print(
            "---------------------------"
        )
        print(
            f"Mesh:    {invite['mesh_name']}"
        )
        print(
            f"Mesh ID: {invite['mesh_id']}"
        )
        print()
        print("Join Token:")
        print(
            invite["token"]
        )
        print()
        print(
            f"Expires: {invite['expires_at']}"
        )

    except ValueError as exc:
        print(
            f"Error: {exc}"
        )


def mesh_join(
    token: str,
    controller_url: str | None = None,
):
    identity = NodeIdentityService()
    node = identity.get_node()

    print("Hyperspace Mesh Join")
    print("--------------------")

    if controller_url:
        print("Using explicit controller...")
    else:
        print("Searching for controller on LAN...")

    print()

    try:
        from urllib.parse import urlparse

        resolved_controller = resolve_join_controller(
            controller_url=controller_url,
            timeout=10,
        )

        parsed = urlparse(
            resolved_controller
        )

        controller_host = parsed.hostname

        if not controller_host:
            raise RuntimeError(
                "Invalid controller URL."
            )

        # IMPORTANT:
        # Controller API = 8000
        # Hyperspace TCP mesh transport = 8765
        controller_port = 8765

        print("Controller resolved")
        print("-------------------")
        print(
            f"Controller: "
            f"{controller_host}:{controller_port}"
        )
        print(
            f"API:        "
            f"{resolved_controller}"
        )
        print(
            f"Node ID:   "
            f"{node.node_id}"
        )
        print()

        print(
            "Sending join request..."
        )

        payload = {
            "message_type": "mesh_join_request",
            "token": token,
            "node_id": node.node_id,
            "hostname": node.hostname,
            "platform": node.platform,
            "ip_address": node.ip_address,
            "port": node.port,
        }

        transport = TCPTransport()

        response = transport.send_json(
            controller_host,
            controller_port,
            payload,
        )

        print()
        print("Join Response")
        print("-------------")
        print(response)

        if isinstance(response, dict):
            accepted = response.get("accepted")
            status = response.get("status")
            mesh_id = response.get("mesh_id")
            reason = response.get("reason")

            if accepted is not None:
                print(
                    f"Accepted: {accepted}"
                )

            if status is not None:
                print(
                    f"Status:   {status}"
                )

            if mesh_id is not None:
                print(
                    f"Mesh ID:  {mesh_id}"
                )

            if reason is not None:
                print(
                    f"Reason:   {reason}"
                )

        # M20.8.2
        # Return the actual controller response so the
        # caller can persist the successful join state.
        return response

    except Exception as exc:
        print()
        print("Join failed")
        print(
            f"Reason: {exc}"
        )

        return {
            "message_type": "error",
            "accepted": False,
            "reason": str(exc),
        }


def mesh_members():
    membership = MeshMembershipService()

    members = membership.list_members()

    print(
        "Hyperspace Mesh Members"
    )
    print(
        "-----------------------"
    )

    if not members:
        print(
            "No members registered."
        )
        return

    for member in members:
        print()
        print(
            f"Node ID:    "
            f"{member.node_id}"
        )
        print(
            f"Hostname:   "
            f"{member.hostname}"
        )
        print(
            f"Platform:   "
            f"{member.platform}"
        )
        print(
            f"Address:    "
            f"{member.ip_address}:"
            f"{member.port}"
        )
        print(
            f"Mesh ID:    "
            f"{member.mesh_id}"
        )
        print(
            f"Status:     "
            f"{member.status.value}"
        )
        print(
            f"Requested:  "
            f"{member.requested_at}"
        )


def mesh_approve(node_id: str):
    membership = MeshMembershipService()

    try:
        member = membership.approve(
            node_id
        )

        print(
            "Mesh Member Approved"
        )
        print(
            "--------------------"
        )
        print(
            f"Node ID:  "
            f"{member.node_id}"
        )
        print(
            f"Hostname: "
            f"{member.hostname}"
        )
        print(
            f"Status:   "
            f"{member.status.value}"
        )

    except ValueError as exc:
        print(
            f"Error: {exc}"
        )


def mesh_reject(node_id: str):
    membership = MeshMembershipService()

    try:
        member = membership.reject(
            node_id
        )

        print(
            "Mesh Member Rejected"
        )
        print(
            "--------------------"
        )
        print(
            f"Node ID:  "
            f"{member.node_id}"
        )
        print(
            f"Hostname: "
            f"{member.hostname}"
        )
        print(
            f"Status:   "
            f"{member.status.value}"
        )

    except ValueError as exc:
        print(
            f"Error: {exc}"
        )


# ============================================================
# NODE
# ============================================================

def node_status():
    data = controller_get(
        "/api/nodes"
    )

    print(
        "Hyperspace Nodes"
    )
    print(
        "----------------"
    )

    nodes = data.get(
        "nodes",
        []
    )

    if not nodes:
        print(
            "No nodes registered."
        )
        return

    for node in nodes:
        print()
        print(
            f"Node ID:  "
            f"{node.get('node_id')}"
        )
        print(
            f"Hostname: "
            f"{node.get('hostname')}"
        )
        print(
            f"IP:       "
            f"{node.get('ip_address')}"
        )
        print(
            f"Port:     "
            f"{node.get('port')}"
        )
        print(
            f"Status:   "
            f"{node.get('status')}"
        )


def node_identity():
    data = controller_get(
        "/api/nodes"
    )

    nodes = data.get(
        "nodes",
        []
    )

    if not nodes:
        print(
            "No node identity available."
        )
        return

    node = nodes[0]

    print(
        "Node Identity"
    )
    print(
        "-------------"
    )
    print(
        f"Node ID:  "
        f"{node.get('node_id')}"
    )
    print(
        f"Hostname: "
        f"{node.get('hostname')}"
    )
    print(
        f"Platform: "
        f"{node.get('platform')}"
    )
    print(
        f"IP:       "
        f"{node.get('ip_address')}"
    )
    print(
        f"Port:     "
        f"{node.get('port')}"
    )


def node_resources():
    data = controller_get(
        "/api/resources"
    )

    print(
        "Hyperspace Node Resources"
    )
    print(
        "-------------------------"
    )
    print(data)


# ============================================================
# RESOURCES
# ============================================================

def resource_list():
    data = controller_get(
        "/api/resources"
    )

    print(
        "Hyperspace Resource Pool"
    )
    print(
        "------------------------"
    )
    print(data)


def resource_available():
    data = controller_get(
        "/api/resources/available"
    )

    print(
        "Available Resources"
    )
    print(
        "-------------------"
    )
    print(data)


# ============================================================
# JOBS
# ============================================================

def job_submit(message: str):
    payload = {
        "job_type": "test",
        "payload": {
            "message": message,
        },
    }

    data = controller_post(
        "/api/jobs",
        payload,
    )

    print(
        "Job Submitted"
    )
    print(
        "-------------"
    )
    print(
        f"Job ID: "
        f"{data.get('job_id')}"
    )
    print(
        f"Status: "
        f"{data.get('status')}"
    )


def job_list():
    data = controller_get(
        "/api/jobs"
    )

    print(
        "Hyperspace Jobs"
    )
    print(
        "---------------"
    )

    jobs = data.get(
        "jobs",
        []
    )

    if not jobs:
        print(
            "No jobs found."
        )
        return

    for job in jobs:
        print(
            f"{job.get('job_id')} | "
            f"{job.get('status')} | "
            f"{job.get('job_type')}"
        )


def job_status(job_id: str):
    data = controller_get(
        f"/api/jobs/{job_id}"
    )

    print(
        "Job Status"
    )
    print(
        "----------"
    )
    print(
        f"Job ID:  "
        f"{data.get('job_id')}"
    )
    print(
        f"Type:    "
        f"{data.get('job_type')}"
    )
    print(
        f"Status:  "
        f"{data.get('status')}"
    )
    print(
        f"Payload: "
        f"{data.get('payload')}"
    )


def job_cancel(job_id: str):
    data = controller_post(
        f"/api/jobs/{job_id}/cancel"
    )

    print(
        "Job Cancellation"
    )
    print(
        "----------------"
    )
    print(
        f"Job ID: {job_id}"
    )
    print(
        f"Result: {data}"
    )


# ============================================================
# SCHEDULER
# ============================================================

def scheduler_assign(job_id: str):
    data = controller_post(
        "/api/scheduler/assign",
        {
            "job_id": job_id,
        },
    )

    print(
        "Scheduler Assignment"
    )
    print(
        "--------------------"
    )
    print(
        f"Job ID:   "
        f"{data.get('job_id')}"
    )
    print(
        f"Node ID:  "
        f"{data.get('node_id')}"
    )
    print(
        f"Score:    "
        f"{data.get('score')}"
    )
    print(
        f"CPU:      "
        f"{data.get('assigned_cpu_threads')}"
    )
    print(
        f"RAM:      "
        f"{data.get('assigned_ram_gb')}"
    )
    print(
        f"GPU:      "
        f"{data.get('assigned_gpu_count')}"
    )
    print(
        f"VRAM:     "
        f"{data.get('assigned_vram_gb')}"
    )
    print(
        f"Status:   "
        f"{data.get('status')}"
    )


# ============================================================
# ARTIFACT DISPLAY
# ============================================================

def print_artifact(artifact):
    if not artifact:
        return

    print()
    print(
        "Artifact"
    )
    print(
        "--------"
    )
    print(
        f"ID:   "
        f"{artifact.get('artifact_id')}"
    )
    print(
        f"Name: "
        f"{artifact.get('name')}"
    )
    print(
        f"Type: "
        f"{artifact.get('artifact_type')}"
    )
    print(
        f"Path: "
        f"{artifact.get('path')}"
    )
    print(
        f"Size: "
        f"{artifact.get('size_bytes')} bytes"
    )


# ============================================================
# EXECUTION
# ============================================================

def execution_run(job_id: str):
    try:
        # ----------------------------------------------------
        # 1. Verify job exists
        # ----------------------------------------------------

        job_response = requests.get(
            f"{CONTROLLER_API}/api/jobs/{job_id}",
            timeout=10,
        )

        job_response.raise_for_status()

        # ----------------------------------------------------
        # 2. Ask scheduler for assignment
        # ----------------------------------------------------

        assignment_response = requests.post(
            f"{CONTROLLER_API}/api/scheduler/assign",
            json={
                "job_id": job_id,
            },
            timeout=10,
        )

        assignment_response.raise_for_status()

        assignment = (
            assignment_response.json()
        )

        # ----------------------------------------------------
        # 3. Execute assigned job
        # ----------------------------------------------------

        response = requests.post(
            f"{CONTROLLER_API}/api/execution",
            json={
                "job_id": job_id,
                "assignment": assignment,
            },
            timeout=30,
        )

        response.raise_for_status()

        data = response.json()

        print(
            "Execution"
        )
        print(
            "---------"
        )
        print(
            f"Execution ID: "
            f"{data.get('execution_id')}"
        )
        print(
            f"Job ID:       "
            f"{data.get('job_id')}"
        )
        print(
            f"Success:      "
            f"{data.get('success')}"
        )
        print(
            f"Output:       "
            f"{data.get('output')}"
        )
        print(
            f"Error:        "
            f"{data.get('error')}"
        )

        print_artifact(
            data.get("artifact")
        )

    except requests.HTTPError as exc:
        print_http_error(
            "Execution command",
            exc,
        )

    except Exception as exc:
        print(
            "Execution command failed: "
            f"{exc}"
        )


def execution_distributed(
    job_id: str,
    partition_count: int,
):
    if partition_count < 1:
        print(
            "Partitions must be at least 1."
        )
        return

    try:
        data = controller_post(
            "/api/execution/distributed",
            {
                "job_id": job_id,
                "partition_count": partition_count,
            },
        )

        print(
            "Distributed Execution"
        )
        print(
            "---------------------"
        )
        print(
            f"Execution ID: "
            f"{data.get('execution_id')}"
        )
        print(
            f"Job ID:       "
            f"{data.get('job_id')}"
        )
        print(
            f"Partitions:   "
            f"{data.get('total_partitions', partition_count)}"
        )

        partitions = data.get(
            "partitions",
            []
        )

        if partitions:
            print()
            print(
                "Partitions"
            )
            print(
                "----------"
            )

            for partition in partitions:
                print(
                    f"{partition.get('partition_index')} | "
                    f"Node: "
                    f"{partition.get('assigned_node_id')} | "
                    f"Status: "
                    f"{partition.get('status')}"
                )

        results = data.get(
            "results",
            []
        )

        if results:
            print()
            print(
                "Results"
            )
            print(
                "-------"
            )

            for result in results:
                print(
                    f"Execution: "
                    f"{result.get('execution_id')} | "
                    f"Success: "
                    f"{result.get('success')} | "
                    f"Output: "
                    f"{result.get('output')} | "
                    f"Error: "
                    f"{result.get('error')}"
                )

        artifacts = data.get(
            "artifacts",
            []
        )

        if artifacts:
            for artifact in artifacts:
                print_artifact(
                    artifact
                )

        if data.get("artifact"):
            print_artifact(
                data.get("artifact")
            )

    except requests.HTTPError as exc:
        print_http_error(
            "Distributed execution",
            exc,
        )

    except Exception as exc:
        print(
            "Distributed execution failed: "
            f"{exc}"
        )


def execution_fault_tolerant(
    job_id: str,
):
    try:
        nodes_data = controller_get(
            "/api/nodes"
        )

        candidate_nodes = []

        for node in nodes_data.get(
            "nodes",
            [],
        ):
            status = str(
                node.get(
                    "status",
                    "",
                )
            ).lower()

            if status != "online":
                continue

            candidate_nodes.append(
                {
                    "node_id": node.get(
                        "node_id"
                    ),
                    "host": node.get(
                        "ip_address"
                    ),
                    "port": node.get(
                        "port"
                    ),
                }
            )

        if not candidate_nodes:
            print(
                "No online candidate nodes."
            )
            return

        data = controller_post(
            "/api/execution/fault-tolerant",
            {
                "job_id": job_id,
                "candidate_nodes": candidate_nodes,
            },
        )

        print(
            "Fault-Tolerant Execution"
        )
        print(
            "------------------------"
        )
        print(
            f"Execution ID: "
            f"{data.get('execution_id')}"
        )
        print(
            f"Job ID:       "
            f"{data.get('job_id')}"
        )
        print(
            f"Success:      "
            f"{data.get('success')}"
        )
        print(
            f"Output:       "
            f"{data.get('output')}"
        )
        print(
            f"Error:        "
            f"{data.get('error')}"
        )

        print_artifact(
            data.get("artifact")
        )

        artifacts = data.get(
            "artifacts",
            []
        )

        for artifact in artifacts:
            if (
                data.get("artifact")
                and artifact.get("artifact_id")
                == data["artifact"].get("artifact_id")
            ):
                continue

            print_artifact(
                artifact
            )

    except requests.HTTPError as exc:
        print_http_error(
            "Fault-tolerant execution",
            exc,
        )

    except Exception as exc:
        print(
            "Fault-tolerant execution failed: "
            f"{exc}"
        )


# ============================================================
# ARTIFACTS
# ============================================================

def artifact_list():
    try:
        data = controller_get(
            "/api/artifacts"
        )

        print(
            "Hyperspace Artifacts"
        )
        print(
            "--------------------"
        )

        artifacts = data.get(
            "artifacts",
            []
        )

        if not artifacts:
            print(
                "No artifacts found."
            )
            return

        for artifact in artifacts:
            print()
            print(
                f"ID:   "
                f"{artifact.get('artifact_id')}"
            )
            print(
                f"Name: "
                f"{artifact.get('name')}"
            )
            print(
                f"Type: "
                f"{artifact.get('artifact_type')}"
            )
            print(
                f"Job:  "
                f"{artifact.get('job_id')}"
            )
            print(
                f"Size: "
                f"{artifact.get('size_bytes')} bytes"
            )

    except requests.HTTPError as exc:
        print_http_error(
            "Artifact list",
            exc,
        )

    except Exception as exc:
        print(
            "Artifact list failed: "
            f"{exc}"
        )


def artifact_status(
    artifact_id: str,
):
    try:
        data = controller_get(
            f"/api/artifacts/{artifact_id}"
        )

        print(
            "Artifact Status"
        )
        print(
            "---------------"
        )

        print(
            f"ID:          "
            f"{data.get('artifact_id')}"
        )
        print(
            f"Name:        "
            f"{data.get('name')}"
        )
        print(
            f"Type:        "
            f"{data.get('artifact_type')}"
        )
        print(
            f"Job ID:      "
            f"{data.get('job_id')}"
        )
        print(
            f"Path:        "
            f"{data.get('path')}"
        )
        print(
            f"Size:        "
            f"{data.get('size_bytes')} bytes"
        )

    except requests.HTTPError as exc:
        print_http_error(
            "Artifact status",
            exc,
        )

    except Exception as exc:
        print(
            "Artifact status failed: "
            f"{exc}"
        )


# ============================================================
# GPU
# ============================================================

def gpu_list():
    try:
        data = controller_get(
            "/api/gpus"
        )

        print(
            "Hyperspace GPUs"
        )
        print(
            "---------------"
        )

        gpus = data.get(
            "gpus",
            []
        )

        if not gpus:
            print(
                "No GPUs registered."
            )
            return

        for gpu in gpus:
            print()
            print(
                f"Node ID:       "
                f"{gpu.get('node_id')}"
            )
            print(
                f"GPU ID:        "
                f"{gpu.get('id')}"
            )
            print(
                f"Name:          "
                f"{gpu.get('name')}"
            )
            print(
                f"VRAM Total:    "
                f"{gpu.get('vram_total_gb')} GB"
            )
            print(
                f"VRAM Available:"
                f" {gpu.get('vram_available_gb')} GB"
            )
            print(
                f"Utilization:   "
                f"{gpu.get('utilization_percent')}%"
            )
            print(
                f"Temperature:   "
                f"{gpu.get('temperature_c')} C"
            )
            print(
                f"Available:     "
                f"{gpu.get('available')}"
            )

    except requests.HTTPError as exc:
        print_http_error(
            "GPU list",
            exc,
        )

    except Exception as exc:
        print(
            "GPU list failed: "
            f"{exc}"
        )


def gpu_status():
    try:
        data = controller_get(
            "/api/gpus"
        )

        print(
            "Hyperspace GPU Status"
        )
        print(
            "---------------------"
        )

        gpus = data.get(
            "gpus",
            []
        )

        if not gpus:
            print(
                "No GPUs registered."
            )
            return

        for gpu in gpus:
            print()
            print(
                f"{gpu.get('node_id')}:"
                f"{gpu.get('id')} | "
                f"{gpu.get('name')} | "
                f"VRAM "
                f"{gpu.get('vram_available_gb')}/"
                f"{gpu.get('vram_total_gb')} GB | "
                f"Utilization "
                f"{gpu.get('utilization_percent')}% | "
                f"Available "
                f"{gpu.get('available')}"
            )

    except requests.HTTPError as exc:
        print_http_error(
            "GPU status",
            exc,
        )

    except Exception as exc:
        print(
            "GPU status failed: "
            f"{exc}"
        )


# ============================================================
# MAIN CLI
# ============================================================

def main():

    global CONTROLLER_API

    parser = argparse.ArgumentParser(
        prog="hyperspace",
        description=(
            "Hyperspace distributed "
            "compute mesh CLI"
        ),
    )

    # --------------------------------------------------------
    # GLOBAL OPTIONS
    # --------------------------------------------------------

    parser.add_argument(
        "--version",
        action="version",
        version=f"Hyperspace {VERSION}",
    )

    parser.add_argument(
        "--controller",
        default=None,
        help=(
            "Controller API URL "
            "(default: HYPERSPACE_CONTROLLER "
            "or http://localhost:8000)"
        ),
    )

    # --------------------------------------------------------
    # COMMANDS
    # --------------------------------------------------------

    subparsers = parser.add_subparsers(
        dest="command"
    )


    install_parser = subparsers.add_parser(
        "install",
        help="Manage the Hyperspace installation",
    )

    install_subparsers = install_parser.add_subparsers(
        dest="install_command"
    )

    install_subparsers.add_parser(
        "status",
        help="Show installation status",
    )

    install_subparsers.add_parser(
        "verify",
        help="Verify installation integrity",
    )

    install_subparsers.add_parser(
        "upgrade",
        help="Upgrade the Hyperspace installation",
    )



    # ========================================================
    # STATUS
    # ========================================================

    subparsers.add_parser(
        "status",
        help=(
            "Show Hyperspace "
            "controller status"
        ),
    )

    # ========================================================
    # BOOTSTRAP
    # ========================================================

    bootstrap_parser = subparsers.add_parser(
        "bootstrap",
        help="Initialize the local Hyperspace runtime",
    )

    bootstrap_parser.add_argument(
        "--join",
        metavar="TOKEN",
        default=None,
        help="Bootstrap this node and join a mesh using an invitation token",
    )

    subparsers.add_parser(
        "doctor",
        help="Validate the Hyperspace runtime environment",
    )

    # ========================================================
    # NODES
    # ========================================================

    subparsers.add_parser(
        "nodes",
        help="Show connected nodes",
    )

    # ========================================================
    # NODE
    # ========================================================

    node_parser = subparsers.add_parser(
        "node",
        help="Manage local node",
    )

    node_subparsers = (
        node_parser.add_subparsers(
            dest="node_command"
        )
    )

    node_subparsers.add_parser(
        "status",
        help="Show node status",
    )

    node_subparsers.add_parser(
        "identity",
        help="Show node identity",
    )

    node_subparsers.add_parser(
        "resources",
        help="Show node resources",
    )

    # ========================================================
    # MESH
    # ========================================================

    mesh_parser = subparsers.add_parser(
        "mesh",
        help="Manage Hyperspace mesh",
    )

    mesh_subparsers = (
        mesh_parser.add_subparsers(
            dest="mesh_command"
        )
    )

    create_parser = (
        mesh_subparsers.add_parser(
            "create",
            help="Create a new mesh",
        )
    )

    create_parser.add_argument(
        "name",
        help="Mesh name",
    )

    mesh_subparsers.add_parser(
        "status",
        help="Show mesh status",
    )

    mesh_subparsers.add_parser(
        "invite",
        help="Create a mesh invitation",
    )

    join_parser = (
        mesh_subparsers.add_parser(
            "join",
            help=(
                "Join a mesh using "
                "an invitation token"
            ),
        )
    )

    join_parser.add_argument(
        "token",
        help="Mesh invitation token",
    )

    mesh_subparsers.add_parser(
        "members",
        help="List mesh members",
    )

    mesh_subparsers.add_parser(
        "join-payload",
        help="Generate a portable mesh join payload",
    )

    approve_parser = (
        mesh_subparsers.add_parser(
            "approve",
            help=(
                "Approve a pending "
                "mesh member"
            ),
        )
    )

    approve_parser.add_argument(
        "node_id",
        help="Node ID to approve",
    )

    reject_parser = (
        mesh_subparsers.add_parser(
            "reject",
            help="Reject a mesh member",
        )
    )

    reject_parser.add_argument(
        "node_id",
        help="Node ID to reject",
    )

    # ========================================================
    # RESOURCE
    # ========================================================

    resource_parser = (
        subparsers.add_parser(
            "resource",
            help="Manage shared resources",
        )
    )

    resource_subparsers = (
        resource_parser.add_subparsers(
            dest="resource_command"
        )
    )

    resource_subparsers.add_parser(
        "list",
        help="List mesh resources",
    )

    resource_subparsers.add_parser(
        "available",
        help="Show available resources",
    )

    # ========================================================
    # JOB
    # ========================================================

    job_parser = subparsers.add_parser(
        "job",
        help="Manage compute jobs",
    )

    job_subparsers = (
        job_parser.add_subparsers(
            dest="job_command"
        )
    )

    submit_parser = (
        job_subparsers.add_parser(
            "submit",
            help="Submit a compute job",
        )
    )

    submit_parser.add_argument(
        "message",
        nargs="?",
        default="CLI test job",
        help="Job message",
    )

    job_subparsers.add_parser(
        "list",
        help="List compute jobs",
    )

    status_parser = (
        job_subparsers.add_parser(
            "status",
            help="Show job status",
        )
    )

    status_parser.add_argument(
        "job_id",
        help="Job ID",
    )

    cancel_parser = (
        job_subparsers.add_parser(
            "cancel",
            help="Cancel a queued job",
        )
    )

    cancel_parser.add_argument(
        "job_id",
        help="Job ID",
    )

    # ========================================================
    # SCHEDULER
    # ========================================================

    scheduler_parser = (
        subparsers.add_parser(
            "scheduler",
            help="Manage job scheduling",
        )
    )

    scheduler_subparsers = (
        scheduler_parser.add_subparsers(
            dest="scheduler_command"
        )
    )

    assign_parser = (
        scheduler_subparsers.add_parser(
            "assign",
            help=(
                "Assign a job to "
                "the best available node"
            ),
        )
    )

    assign_parser.add_argument(
        "job_id",
        help="Job ID",
    )

    # ========================================================
    # EXECUTION
    # ========================================================

    execution_parser = (
        subparsers.add_parser(
            "execution",
            help="Execute compute jobs",
        )
    )

    execution_subparsers = (
        execution_parser.add_subparsers(
            dest="execution_command"
        )
    )

    run_parser = (
        execution_subparsers.add_parser(
            "run",
            help="Execute a scheduled job",
        )
    )

    run_parser.add_argument(
        "job_id",
        help="Job ID",
    )

    distributed_parser = (
        execution_subparsers.add_parser(
            "distributed",
            help=(
                "Execute a job across "
                "multiple nodes"
            ),
        )
    )

    distributed_parser.add_argument(
        "job_id",
        help="Job ID",
    )

    distributed_parser.add_argument(
        "--partitions",
        type=int,
        default=1,
        help=(
            "Number of execution "
            "partitions"
        ),
    )

    fault_parser = (
        execution_subparsers.add_parser(
            "fault-tolerant",
            help=(
                "Execute a job with "
                "failure recovery"
            ),
        )
    )

    fault_parser.add_argument(
        "job_id",
        help="Job ID",
    )

    # ========================================================
    # ARTIFACT
    # ========================================================

    artifact_parser = (
        subparsers.add_parser(
            "artifact",
            help="Manage execution artifacts",
        )
    )

    artifact_subparsers = (
        artifact_parser.add_subparsers(
            dest="artifact_command"
        )
    )

    artifact_subparsers.add_parser(
        "list",
        help="List artifacts",
    )

    artifact_status_parser = (
        artifact_subparsers.add_parser(
            "status",
            help="Show artifact information",
        )
    )

    artifact_status_parser.add_argument(
        "artifact_id",
        help="Artifact ID",
    )

    # ========================================================
    # GPU
    # ========================================================

    gpu_parser = (
        subparsers.add_parser(
            "gpu",
            help="Manage GPU resources",
        )
    )

    gpu_subparsers = (
        gpu_parser.add_subparsers(
            dest="gpu_command"
        )
    )

    gpu_subparsers.add_parser(
        "list",
        help="List GPUs",
    )

    gpu_subparsers.add_parser(
        "status",
        help="Show GPU status",
    )

    # ========================================================
    # PARSE ARGUMENTS
    # ========================================================

    args = parser.parse_args()

    # ========================================================
    # CONTROLLER OVERRIDE
    # ========================================================

    if args.controller:
        CONTROLLER_API = (
            args.controller.rstrip("/")
        )

    # ============================================================
    # BOOTSTRAP
    # ============================================================



    if args.command == "bootstrap":

        try:

            # ----------------------------------------------------
            # M20.7 — ONE-COMMAND BOOTSTRAP + JOIN
            # ----------------------------------------------------

            if args.join:

                from hyperspace.services.one_command_bootstrap_service import (
                    prepare_one_command_bootstrap,
                )

                result = prepare_one_command_bootstrap()

                print("========================================")
                print("     HYPERSPACE ONE-COMMAND BOOTSTRAP")
                print("========================================")
                print()

                print(
                    f"Node ID          : "
                    f"{result.node_id}"
                )

                print(
                    f"Controller       : "
                    f"{result.controller_url}"
                )

                print(
                    f"Bootstrap        : "
                    f"{'READY' if result.ready else 'FAILED'}"
                )

                print()

                if not result.ready:
                    print(
                        "Bootstrap failed."
                    )
                    return

                print(
                    "Joining mesh..."
                )
                print()

                join_response = mesh_join(
                    args.join,
                    controller_url=result.controller_url,
                )

                # M20.8.2 — Persist successful join state.
                if isinstance(join_response, dict):
                    accepted = join_response.get(
                        "accepted"
                    )

                    if accepted is True:
                        state_service = BootstrapStateService()

                        state_service.mark_joined(
                            node_id=result.node_id,
                            mesh_id=join_response.get(
                                "mesh_id",
                                "",
                            ),
                            controller_url=(
                                result.controller_url or ""
                            ),
                            status=join_response.get(
                                "status",
                                "approved",
                            ),
                        )

                        print()
                        print("Join state saved.")

                return

            # M20.8.2 — PERSIST SUCCESSFUL JOIN STATE
            #
            # mesh_join() prints the existing join response but
            # does not return it. Therefore query the membership
            # state through the existing controller API before
            # persisting local state.
            #
            # We intentionally do not modify the frozen join flow.

            state_service = BootstrapStateService()

            try:
                from hyperspace.services.mesh_membership_service import (
                    MeshMembershipService,
                )

                membership = MeshMembershipService()

                members = membership.list_members()

                joined_member = None

                for member in members:
                    member_node_id = getattr(
                        member,
                        "node_id",
                        None,
                    )

                    if member_node_id == result.node_id:
                        joined_member = member
                        break

                if joined_member is not None:
                    mesh_id = getattr(
                        joined_member,
                        "mesh_id",
                        None,
                    )

                    status = getattr(
                        joined_member,
                        "status",
                        None,
                    )

                    state_service.mark_joined(
                        node_id=result.node_id,
                        mesh_id=(
                            str(mesh_id)
                            if mesh_id
                            else ""
                        ),
                        controller_url=(
                            result.controller_url
                            or ""
                        ),
                        status=(
                            getattr(
                                status,
                                "value",
                                str(status)
                                if status is not None
                                else "approved",
                            )
                        ),
                    )

                    print()
                    print(
                        "Join state saved."
                    )

                else:
                    print()
                    print(
                        "Join accepted. "
                        "Local join state was not persisted "
                        "because membership state is not yet available."
                    )

            except Exception as exc:
                print()
                print(
                    "Warning: could not persist join state: "
                    f"{exc}"
                )

            return

            # ----------------------------------------------------
            # EXISTING BOOTSTRAP FLOW
            # ----------------------------------------------------

            from hyperspace.services.bootstrap_service import (
                bootstrap_node,
            )

            result = bootstrap_node()

            print("========================================")
            print("        HYPERSPACE BOOTSTRAP")
            print("========================================")
            print()

            print(
                f"Runtime          : "
                f"{'READY' if result.runtime_ready else 'FAIL'}"
            )

            print(
                f"Installation     : "
                f"{'READY' if result.installation_ready else 'FAIL'}"
            )

            print(
                f"Environment      : "
                f"{'READY' if result.environment_ready else 'FAIL'}"
            )

            print(
                f"Node Identity    : "
                f"{'READY' if result.node_identity_ready else 'FAIL'}"
            )

            print(
                f"Security         : "
                f"{'READY' if result.security_identity_ready else 'FAIL'}"
            )

            print()

            print(
                f"Node ID          : "
                f"{result.node_id or 'UNAVAILABLE'}"
            )

            print(
                f"Data Directory   : "
                f"{result.data_dir}"
            )

            print()

            print(
                f"Bootstrap        : "
                f"{'READY' if result.ready else 'FAILED'}"
            )

        except Exception as exc:
            print(
                "Bootstrap failed: "
                f"{exc}"
            )

        return



    # ========================================================
    # INSTALLATION
    # ========================================================

    if args.command == "install":

        from hyperspace.infrastructure.runtime import (
            InstallationManager,
        )

        manager = InstallationManager()

        if args.install_command == "status":

            result = manager.status()

            print("Hyperspace Installation")
            print("-----------------------")
            print(f"State:             {result['state']}")
            print(f"Installed:         {result['installed']}")
            print(
                f"Installed version: "
                f"{result['installed_version']}"
            )
            print(
                f"Current version:   "
                f"{result['current_version']}"
            )
            print(
                f"Upgrade available: "
                f"{result['upgrade_available']}"
            )
            print(
                f"Install directory: "
                f"{result['install_dir']}"
            )
            print(
                f"Data directory:    "
                f"{result['data_dir']}"
            )

            return

        if args.install_command == "verify":

            result = manager.verify()

            print("Hyperspace Installation Verification")
            print("-------------------------------------")

            print(
                f"State:      {result['state']}"
            )
            print(
                f"Version:    {result['installed_version']}"
            )
            print(
                f"Directories: {result['directories_ok']}"
            )
            print(
                f"Modules:     {result['modules_ok']}"
            )
            print(
                f"READY:      {result['ready']}"
            )

            return

        if args.install_command == "upgrade":

            try:
                metadata = manager.upgrade()

                print("Hyperspace Installation Upgrade")
                print("--------------------------------")
                print(
                    f"Version: {metadata.version}"
                )
                print(
                    "Runtime data preserved: True"
                )
                print(
                    "Installation upgrade: READY"
                )

            except Exception as exc:
                print(
                    f"Installation upgrade failed: {exc}"
                )

            return

        state = manager.get_state()

        if state == "NEW":

            metadata = manager.initialize()

            print("Hyperspace Installation")
            print("-----------------------")
            print("Installation initialized.")
            print(
                f"Version: {metadata.version}"
            )
            print(
                f"Data directory: "
                f"{metadata.data_dir}"
            )
            print("READY: True")

            return

        print("Hyperspace Installation")
        print("-----------------------")
        print(f"Installation state: {state}")

        if state == "INITIALIZED":
            print("Installation is already initialized.")
            print("Use:")
            print("  hyperspace install status")
            print("  hyperspace install verify")
            print("  hyperspace install upgrade")

        return


    # ========================================================
    # DOCTOR
    # ========================================================

    if args.command == "doctor":
        try:
            from hyperspace.infrastructure.runtime import validate_environment

            result = validate_environment()

            print("Hyperspace Environment")
            print("----------------------")

            for check in result["checks"]:
                status = "OK" if check["status"] else "FAIL"

                print(
                    f"[{status:<4}] "
                    f"{check['name']}: "
                    f"{check['detail']}"
                )

            print()
            print(
                f"Checks: {result['passed']}/{result['total']} passed"
            )
            print(
                f"READY:  {result['ready']}"
            )

        except Exception as exc:
            print(
                "Environment validation failed: "
                f"{exc}"
            )

        return

    # ========================================================
    # DOCTOR
    # ========================================================

    if args.command == "doctor":
        try:
            from hyperspace.infrastructure.runtime import validate_environment

            result = validate_environment()

            print("Hyperspace Environment")
            print("----------------------")

            for check in result["checks"]:
                status = "OK" if check["status"] else "FAIL"

                print(
                    f"[{status:<4}] "
                    f"{check['name']}: "
                    f"{check['detail']}"
                )

            print()
            print(
                f"Checks: {result['passed']}/{result['total']} passed"
            )
            print(
                f"READY:  {result['ready']}"
            )

        except Exception as exc:
            print(
                "Environment validation failed: "
                f"{exc}"
            )

        return

    # ========================================================
    # TOP LEVEL STATUS
    # ========================================================

    if args.command == "status":

        try:
            data = controller_get(
                "/health"
            )

            print(
                "Hyperspace"
            )
            print(
                "----------"
            )
            print(
                f"Status:     "
                f"{data.get('status')}"
            )
            print(
                f"Controller: "
                f"{data.get('controller')}"
            )
            print(
                f"Node ID:    "
                f"{data.get('node_id')}"
            )
            print(
                f"API:        "
                f"{CONTROLLER_API}"
            )

        except requests.HTTPError as exc:
            print_http_error(
                "Controller status",
                exc,
            )

        except Exception as exc:
            print(
                "Controller unavailable."
            )
            print(
                f"Reason: {exc}"
            )

        return

    # ========================================================
    # NODES
    # ========================================================

    if args.command == "nodes":

        try:
            node_status()

        except requests.HTTPError as exc:
            print_http_error(
                "Node listing",
                exc,
            )

        except Exception as exc:
            print(
                "Unable to list nodes: "
                f"{exc}"
            )

        return

  

    # ========================================================
    # MESH
    # ========================================================

    if args.command == "mesh":

        if args.mesh_command == "create":
            mesh_create(
                args.name
            )
            return

        if args.mesh_command == "status":
            mesh_status()
            return

        if args.mesh_command == "invite":
            mesh_invite()
            return

        if args.mesh_command == "join":
            mesh_join(
                args.token,
                controller_url=CONTROLLER_API
                if args.controller
                else None,
            )
            return

        if args.mesh_command == "members":
            mesh_members()
            return

        if args.mesh_command == "approve":
            mesh_approve(
                args.node_id
            )
            return

        if args.mesh_command == "reject":
            mesh_reject(
                args.node_id
            )
            return

        if args.mesh_command == "join-payload":
            try:
                from hyperspace.services.join_payload_service import (
                    create_join_payload,
                )

                payload = create_join_payload()

                print("Hyperspace Mesh Join Payload")
                print("----------------------------")
                print(f"Mesh:       {payload.mesh_name}")
                print(f"Mesh ID:    {payload.mesh_id}")
                print(
                    f"Controller: "
                    f"{payload.controller_host}:"
                    f"{payload.controller_port}"
                )
                print(f"Expires:    {payload.expires_at}")
                print()
                print("Payload:")
                print(payload.encode())

            except ValueError as exc:
                print(f"Error: {exc}")

            except Exception as exc:
                print(
                    "Join payload generation failed: "
                    f"{exc}"
                )

            return

        mesh_parser.print_help()
        return

    # ========================================================
    # NODE
    # ========================================================

    if args.command == "node":

        try:

            if args.node_command == "status":
                node_status()

            elif args.node_command == "identity":
                node_identity()

            elif args.node_command == "resources":
                node_resources()

            else:
                node_parser.print_help()

        except requests.HTTPError as exc:
            print_http_error(
                "Node command",
                exc,
            )

        except Exception as exc:
            print(
                "Node command failed: "
                f"{exc}"
            )

        return

    # ========================================================
    # RESOURCE
    # ========================================================

    if args.command == "resource":

        try:

            if args.resource_command == "list":
                resource_list()

            elif args.resource_command == "available":
                resource_available()

            else:
                resource_parser.print_help()

        except requests.HTTPError as exc:
            print_http_error(
                "Resource command",
                exc,
            )

        except Exception as exc:
            print(
                "Resource command failed: "
                f"{exc}"
            )

        return

    # ========================================================
    # JOB
    # ========================================================

    if args.command == "job":

        try:

            if args.job_command == "submit":
                job_submit(
                    args.message
                )

            elif args.job_command == "list":
                job_list()

            elif args.job_command == "status":
                job_status(
                    args.job_id
                )

            elif args.job_command == "cancel":
                job_cancel(
                    args.job_id
                )

            else:
                job_parser.print_help()

        except requests.HTTPError as exc:
            print_http_error(
                "Job command",
                exc,
            )

        except Exception as exc:
            print(
                "Job command failed: "
                f"{exc}"
            )

        return

    # ========================================================
    # SCHEDULER
    # ========================================================

    if args.command == "scheduler":

        try:

            if args.scheduler_command == "assign":
                scheduler_assign(
                    args.job_id
                )

            else:
                scheduler_parser.print_help()

        except requests.HTTPError as exc:
            print_http_error(
                "Scheduler command",
                exc,
            )

        except Exception as exc:
            print(
                "Scheduler command failed: "
                f"{exc}"
            )

        return

    # ========================================================
    # EXECUTION
    # ========================================================

    if args.command == "execution":

        try:

            if args.execution_command == "run":

                execution_run(
                    args.job_id
                )

            elif (
                args.execution_command
                == "distributed"
            ):

                execution_distributed(
                    args.job_id,
                    args.partitions,
                )

            elif (
                args.execution_command
                == "fault-tolerant"
            ):

                execution_fault_tolerant(
                    args.job_id
                )

            else:

                execution_parser.print_help()

        except Exception as exc:

            print(
                "Execution command failed: "
                f"{exc}"
            )

        return

    # ========================================================
    # ARTIFACT
    # ========================================================

    if args.command == "artifact":

        try:

            if args.artifact_command == "list":

                artifact_list()

            elif (
                args.artifact_command
                == "status"
            ):

                artifact_status(
                    args.artifact_id
                )

            else:

                artifact_parser.print_help()

        except Exception as exc:

            print(
                "Artifact command failed: "
                f"{exc}"
            )

        return

    # ========================================================
    # GPU
    # ========================================================

    if args.command == "gpu":

        try:

            if args.gpu_command == "list":

                gpu_list()

            elif args.gpu_command == "status":

                gpu_status()

            else:

                gpu_parser.print_help()

        except Exception as exc:

            print(
                "GPU command failed: "
                f"{exc}"
            )

        return

    # ============================================================
    # MESH JOIN PAYLOAD
    # ============================================================

    if (
        args.command == "mesh"
        and args.mesh_command == "join-payload"
    ):
        try:
            from hyperspace.services.join_payload_service import (
                create_join_payload,
            )

            payload = create_join_payload()

            print("Hyperspace Mesh Join Payload")
            print("----------------------------")
            print(
                f"Mesh:       {payload.mesh_name}"
            )
            print(
                f"Mesh ID:    {payload.mesh_id}"
            )
            print(
                f"Controller: "
                f"{payload.controller_host}:"
                f"{payload.controller_port}"
            )
            print(
                f"Expires:    {payload.expires_at}"
            )
            print()
            print("Payload:")
            print(payload.encode())

        except ValueError as exc:
            print(f"Error: {exc}")

        except Exception as exc:
            print(
                "Join payload generation failed: "
                f"{exc}"
            )

        return

    # ========================================================
    # DEFAULT HELP
    # ========================================================

    parser.print_help()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()