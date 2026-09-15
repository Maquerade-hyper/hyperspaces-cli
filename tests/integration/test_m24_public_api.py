from __future__ import annotations

import json
import subprocess
import sys
import time
import urllib.error
import urllib.request


HOST = "127.0.0.1"
PORT = 8010
BASE_URL = f"http://{HOST}:{PORT}"


def request(
    method: str,
    path: str,
    payload: dict | None = None,
) -> tuple[int, dict]:

    url = (
        f"{BASE_URL}{path}"
    )

    data = None

    headers = {}

    if payload is not None:

        data = json.dumps(
            payload
        ).encode("utf-8")

        headers[
            "Content-Type"
        ] = "application/json"

    req = urllib.request.Request(
        url=url,
        data=data,
        headers=headers,
        method=method,
    )

    try:

        with urllib.request.urlopen(
            req,
            timeout=5,
        ) as response:

            body = response.read()

            return (
                response.status,
                json.loads(
                    body.decode(
                        "utf-8"
                    )
                ),
            )

    except urllib.error.HTTPError as exc:

        body = exc.read()

        return (
            exc.code,
            json.loads(
                body.decode(
                    "utf-8"
                )
            ),
        )


def wait_for_api(
    process,
    attempts: int = 20,
) -> None:

    for _ in range(attempts):

        if process.poll() is not None:

            raise RuntimeError(
                "Public API process exited."
            )

        try:

            status, _ = request(
                "GET",
                "/health",
            )

            if status == 200:
                return

        except Exception:
            pass

        time.sleep(0.25)

    raise RuntimeError(
        "Public API did not start."
    )


def main() -> None:

    print("=" * 60)
    print("HYPERSPACE M24 PUBLIC COMPUTE API")
    print("=" * 60)

    print()
    print("[1] Starting Public Compute API...")

    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "apps.public_api.main:app",
            "--host",
            HOST,
            "--port",
            str(PORT),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:

        wait_for_api(
            process
        )

        print("    API START: PASS")

        # -------------------------------------------------
        # HEALTH
        # -------------------------------------------------

        print()
        print("[2] Testing API health...")

        status, response = request(
            "GET",
            "/health",
        )

        print(
            "    STATUS:",
            status,
        )

        print(
            "    RESPONSE:",
            response,
        )

        if status != 200:
            raise RuntimeError(
                "Health endpoint failed."
            )

        print("    HEALTH: PASS")

        # -------------------------------------------------
        # API INFORMATION
        # -------------------------------------------------

        print()
        print("[3] Testing API information...")

        status, response = request(
            "GET",
            "/api/v1",
        )

        if status != 200:
            raise RuntimeError(
                "API information endpoint failed."
            )

        print(
            "    VERSION:",
            response["version"],
        )

        print("    API INFORMATION: PASS")

        # -------------------------------------------------
        # NODE
        # -------------------------------------------------

        print()
        print("[4] Registering compute node...")

        node_payload = {
            "node_id": "m24-test-node",
            "hostname": "m24-host",
            "cpu_cores": 8,
            "ram_mb": 16384,
            "gpu_count": 1,
        }

        status, response = request(
            "POST",
            "/api/v1/nodes",
            node_payload,
        )

        print(
            "    STATUS:",
            status,
        )

        if status != 200:
            raise RuntimeError(
                "Node registration failed."
            )

        print(
            "    NODE:",
            response["node"]["node_id"],
        )

        print("    NODE REGISTRATION: PASS")

        # -------------------------------------------------
        # RESOURCE
        # -------------------------------------------------

        print()
        print("[5] Reading resources...")

        status, response = request(
            "GET",
            "/api/v1/resources",
        )

        print(
            "    CPU:",
            response["cpu_cores"],
        )

        print(
            "    RAM:",
            response["ram_mb"],
        )

        print(
            "    GPU:",
            response["gpu_count"],
        )

        if status != 200:
            raise RuntimeError(
                "Resource API failed."
            )

        if response["cpu_cores"] != 8:
            raise RuntimeError(
                "Resource CPU total incorrect."
            )

        print("    RESOURCE API: PASS")

        # -------------------------------------------------
        # JOB SUBMISSION
        # -------------------------------------------------

        print()
        print("[6] Submitting compute job...")

        job_payload = {
            "job_type": "python",
            "payload": {
                "code": "print('hello hyperspace')",
            },
            "requirements": {
                "cpu": 1,
                "ram_mb": 512,
            },
        }

        status, response = request(
            "POST",
            "/api/v1/jobs",
            job_payload,
        )

        print(
            "    STATUS:",
            status,
        )

        if status != 200:
            raise RuntimeError(
                "Job submission failed."
            )

        job_id = response[
            "job_id"
        ]

        print(
            "    JOB ID:",
            job_id,
        )

        print(
            "    JOB STATUS:",
            response["status"],
        )

        if response["status"] != "queued":
            raise RuntimeError(
                "Job was not queued."
            )

        print("    JOB SUBMISSION: PASS")

        # -------------------------------------------------
        # JOB LOOKUP
        # -------------------------------------------------

        print()
        print("[7] Reading submitted job...")

        status, response = request(
            "GET",
            f"/api/v1/jobs/{job_id}",
        )

        if status != 200:
            raise RuntimeError(
                "Job lookup failed."
            )

        if response["job_id"] != job_id:
            raise RuntimeError(
                "Job ID mismatch."
            )

        print(
            "    STATUS:",
            response["status"],
        )

        print("    JOB LOOKUP: PASS")

        # -------------------------------------------------
        # RESULT
        # -------------------------------------------------

        print()
        print("[8] Checking job result...")

        status, response = request(
            "GET",
            f"/api/v1/jobs/{job_id}/result",
        )

        if status != 200:
            raise RuntimeError(
                "Result API failed."
            )

        print(
            "    AVAILABLE:",
            response["available"],
        )

        if response["available"]:
            raise RuntimeError(
                "New job unexpectedly has a result."
            )

        print("    RESULT API: PASS")

        # -------------------------------------------------
        # CANCEL
        # -------------------------------------------------

        print()
        print("[9] Cancelling queued job...")

        status, response = request(
            "DELETE",
            f"/api/v1/jobs/{job_id}",
        )

        if status != 200:
            raise RuntimeError(
                "Job cancellation failed."
            )

        print(
            "    CANCELLED:",
            response["cancelled"],
        )

        if not response["cancelled"]:
            raise RuntimeError(
                "Job was not cancelled."
            )

        print("    JOB CONTROL: PASS")

        # -------------------------------------------------
        # NODE LIST
        # -------------------------------------------------

        print()
        print("[10] Listing compute nodes...")

        status, response = request(
            "GET",
            "/api/v1/nodes",
        )

        if status != 200:
            raise RuntimeError(
                "Node listing failed."
            )

        if response["count"] != 1:
            raise RuntimeError(
                "Unexpected node count."
            )

        print(
            "    NODE COUNT:",
            response["count"],
        )

        print("    NODE LIST: PASS")

        # -------------------------------------------------
        # JOB LIST
        # -------------------------------------------------

        print()
        print("[11] Listing jobs...")

        status, response = request(
            "GET",
            "/api/v1/jobs",
        )

        if status != 200:
            raise RuntimeError(
                "Job listing failed."
            )

        if response["count"] != 1:
            raise RuntimeError(
                "Unexpected job count."
            )

        print(
            "    JOB COUNT:",
            response["count"],
        )

        print("    JOB LIST: PASS")

        # -------------------------------------------------
        # FINAL
        # -------------------------------------------------

        print()
        print("=" * 60)
        print("M24 RESULT: PASS")
        print("=" * 60)

        print("M24.1 API MODELS: PASS")
        print("M24.2 COMPUTE API: PASS")
        print("M24.3 NODE / RESOURCE API: PASS")
        print("M24.4 JOB / RESULT API: PASS")
        print("M24.5 PUBLIC API INTEGRATION: PASS")

        print()
        print(
            "HYPERSPACE PUBLIC COMPUTE API: COMPLETE"
        )

        print("=" * 60)

    finally:

        process.terminate()

        try:
            process.wait(
                timeout=3
            )
        except subprocess.TimeoutExpired:
            process.kill()


if __name__ == "__main__":
    main()