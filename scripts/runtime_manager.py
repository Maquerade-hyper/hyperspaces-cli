from __future__ import annotations

import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "data" / "logs"
LOG_FILE = LOG_DIR / "startup.log"

CONTROLLER_HOST = "127.0.0.1"
CONTROLLER_PORT = 8000

AGENT_HOST = "127.0.0.1"
AGENT_PORT = 8765

CONTROLLER_HEALTH_URL = (
    f"http://{CONTROLLER_HOST}:{CONTROLLER_PORT}/health"
)


def log(message: str) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"

    print(line)

    with LOG_FILE.open("a", encoding="utf-8") as file:
        file.write(line + "\n")


def port_is_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection(
            (host, port),
            timeout=1,
        ):
            return True
    except OSError:
        return False


def controller_is_running() -> bool:
    if not port_is_open(
        CONTROLLER_HOST,
        CONTROLLER_PORT,
    ):
        return False

    try:
        response = requests.get(
            CONTROLLER_HEALTH_URL,
            timeout=2,
        )

        return response.ok

    except requests.RequestException:
        return False


def agent_is_running() -> bool:
    return port_is_open(
        AGENT_HOST,
        AGENT_PORT,
    )


def python_executable() -> str:
    executable = Path(sys.executable)

    if executable.exists():
        return str(executable)

    return sys.executable


def start_controller() -> subprocess.Popen:
    log("Starting Hyperspace Controller...")

    process = subprocess.Popen(
        [
            python_executable(),
            "-m",
            "apps.control_plane.main",
        ],
        cwd=str(ROOT),
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
    )

    log(f"Controller process started: PID {process.pid}")

    return process


def start_agent() -> subprocess.Popen:
    log("Starting Hyperspace Agent...")

    process = subprocess.Popen(
        [
            python_executable(),
            "-m",
            "apps.agent.main",
        ],
        cwd=str(ROOT),
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
    )

    log(f"Agent process started: PID {process.pid}")

    return process


def wait_for_controller(
    timeout: int = 15,
) -> bool:
    log("Waiting for Controller health...")

    deadline = time.time() + timeout

    while time.time() < deadline:
        if controller_is_running():
            log("Controller health check: OK")
            return True

        time.sleep(0.5)

    log("Controller health check: TIMEOUT")
    return False


def wait_for_agent(
    timeout: int = 15,
) -> bool:
    log("Waiting for Agent TCP port...")

    deadline = time.time() + timeout

    while time.time() < deadline:
        if agent_is_running():
            log("Agent TCP port check: OK")
            return True

        time.sleep(0.5)

    log("Agent TCP port check: TIMEOUT")
    return False


def terminate_process(
    process: subprocess.Popen | None,
    name: str,
) -> None:
    if process is None:
        return

    if process.poll() is not None:
        return

    log(f"Stopping {name}: PID {process.pid}")

    try:
        process.terminate()
        process.wait(timeout=5)

    except subprocess.TimeoutExpired:
        log(
            f"{name} did not stop gracefully. "
            f"Force terminating PID {process.pid}."
        )

        process.kill()

        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            pass

    log(f"{name} stopped.")


def run() -> int:
    controller_process: subprocess.Popen | None = None
    agent_process: subprocess.Popen | None = None

    log("=" * 50)
    log("HYPERSPACE RUNTIME MANAGER")
    log("=" * 50)

    try:
        # ---------------------------------------------------------
        # CONTROLLER
        # ---------------------------------------------------------

        if controller_is_running():
            log(
                "Controller already running. "
                "Duplicate startup prevented."
            )
        else:
            if port_is_open(
                CONTROLLER_HOST,
                CONTROLLER_PORT,
            ):
                log(
                    "ERROR: Port 8000 is already occupied "
                    "but Hyperspace Controller health check failed."
                )

                log(
                    "Controller will NOT be started."
                )

                return 1

            controller_process = start_controller()

            if not wait_for_controller():
                log(
                    "ERROR: Controller failed to become healthy."
                )

                terminate_process(
                    controller_process,
                    "Controller",
                )

                return 1

        # ---------------------------------------------------------
        # AGENT
        # ---------------------------------------------------------

        if agent_is_running():
            log(
                "Agent already running. "
                "Duplicate startup prevented."
            )
        else:
            agent_process = start_agent()

            if not wait_for_agent():
                log(
                    "ERROR: Agent failed to open TCP port 8765."
                )

                terminate_process(
                    agent_process,
                    "Agent",
                )

                return 1

        # ---------------------------------------------------------
        # READY
        # ---------------------------------------------------------

        log("")
        log("Hyperspace runtime is READY.")
        log(f"Controller: http://{CONTROLLER_HOST}:{CONTROLLER_PORT}")
        log(f"Agent:      {AGENT_HOST}:{AGENT_PORT}")
        log("")
        log("Press Ctrl+C to stop processes started by this manager.")
        log("")

        while True:
            # If this manager started the Controller,
            # detect unexpected termination.
            if (
                controller_process is not None
                and controller_process.poll() is not None
            ):
                log(
                    "WARNING: Controller process terminated."
                )

                controller_process = None

            # If this manager started the Agent,
            # detect unexpected termination.
            if (
                agent_process is not None
                and agent_process.poll() is not None
            ):
                log(
                    "WARNING: Agent process terminated."
                )

                agent_process = None

            time.sleep(2)

    except KeyboardInterrupt:
        log("")
        log("Shutdown requested.")

    except Exception as exc:
        log(f"Runtime manager error: {exc}")
        return 1

    finally:
        # Only terminate processes that THIS manager started.
        terminate_process(
            agent_process,
            "Agent",
        )

        terminate_process(
            controller_process,
            "Controller",
        )

        log("Hyperspace runtime manager stopped.")

    return 0


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()