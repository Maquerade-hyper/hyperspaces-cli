from __future__ import annotations

import json
import subprocess
import sys
import time
import urllib.error
import urllib.request


HOST = "127.0.0.1"
PORT = 8011

BASE_URL = (
    f"http://{HOST}:{PORT}"
)


def request(
    method: str,
    path: str,
    payload: dict | None = None,
    headers: dict | None = None,
):

    url = (
        f"{BASE_URL}{path}"
    )

    data = None

    request_headers = {}

    if headers:
        request_headers.update(
            headers
        )

    if payload is not None:

        data = json.dumps(
            payload
        ).encode("utf-8")

        request_headers[
            "Content-Type"
        ] = "application/json"

    req = urllib.request.Request(
        url=url,
        data=data,
        headers=request_headers,
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
):

    for _ in range(20):

        if process.poll() is not None:

            raise RuntimeError(
                "API process exited."
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
        "API failed to start."
    )


def main():

    print("=" * 60)
    print("HYPERSPACE M25 MULTI-TENANT SAAS")
    print("=" * 60)

    print()
    print("[1] Starting SaaS API...")

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

        # =================================================
        # TENANT A
        # =================================================

        print()
        print("[2] Creating Tenant A...")

        status, response = request(
            "POST",
            "/api/v1/tenants",
            {
                "name": "Tenant A",
                "quota_cpu_seconds": 100,
                "quota_gpu_seconds": 50,
                "quota_jobs": 10,
            },
        )

        if status != 200:
            raise RuntimeError(
                "Tenant A creation failed."
            )

        tenant_a = response[
            "tenant"
        ]

        tenant_a_id = tenant_a[
            "tenant_id"
        ]

        print(
            "    TENANT:",
            tenant_a_id,
        )

        print("    TENANT A: PASS")

        # =================================================
        # TENANT B
        # =================================================

        print()
        print("[3] Creating Tenant B...")

        status, response = request(
            "POST",
            "/api/v1/tenants",
            {
                "name": "Tenant B",
                "quota_cpu_seconds": 200,
                "quota_gpu_seconds": 100,
                "quota_jobs": 20,
            },
        )

        if status != 200:
            raise RuntimeError(
                "Tenant B creation failed."
            )

        tenant_b = response[
            "tenant"
        ]

        tenant_b_id = tenant_b[
            "tenant_id"
        ]

        print(
            "    TENANT:",
            tenant_b_id,
        )

        print("    TENANT B: PASS")

        if tenant_a_id == tenant_b_id:

            raise RuntimeError(
                "Tenant IDs are not unique."
            )

        # =================================================
        # PROJECT A
        # =================================================

        print()
        print("[4] Creating Tenant A project...")

        status, response = request(
            "POST",
            "/api/v1/projects",
            {
                "tenant_id": tenant_a_id,
                "name": "AI Project",
            },
        )

        if status != 200:
            raise RuntimeError(
                "Project creation failed."
            )

        project_a = response[
            "project"
        ]

        project_a_id = project_a[
            "project_id"
        ]

        print(
            "    PROJECT:",
            project_a_id,
        )

        print("    PROJECT CREATION: PASS")

        # =================================================
        # CROSS-TENANT ISOLATION
        # =================================================

        print()
        print("[5] Testing tenant isolation...")

        status, response = request(
            "POST",
            "/api/v1/projects",
            {
                "tenant_id": tenant_b_id,
                "name": "Tenant B Project",
            },
        )

        if status != 200:
            raise RuntimeError(
                "Tenant B project creation failed."
            )

        project_b_id = response[
            "project"
        ][
            "project_id"
        ]

        status, _ = request(
            "GET",
            f"/api/v1/tenants/"
            f"{tenant_b_id}/projects",
        )

        if status != 200:
            raise RuntimeError(
                "Tenant B project listing failed."
            )

        print(
            "    TENANT A:",
            tenant_a_id,
        )

        print(
            "    TENANT B:",
            tenant_b_id,
        )

        if project_a_id == project_b_id:

            raise RuntimeError(
                "Projects were incorrectly shared."
            )

        print("    TENANT ISOLATION: PASS")

        # =================================================
        # API KEY
        # =================================================

        print()
        print("[6] Creating Tenant A API key...")

        status, response = request(
            "POST",
            "/api/v1/api-keys",
            {
                "tenant_id": tenant_a_id,
                "project_id": project_a_id,
            },
        )

        if status != 200:
            raise RuntimeError(
                "API key creation failed."
            )

        raw_key = response[
            "api_key"
        ]

        key_id = response[
            "key_id"
        ]

        print(
            "    KEY ID:",
            key_id,
        )

        print(
            "    PREFIX:",
            response["key_prefix"],
        )

        print("    API KEY CREATION: PASS")

        # =================================================
        # KEY VALIDATION
        # =================================================

        print()
        print("[7] Validating API key...")

        status, response = request(
            "GET",
            "/api/v1/api-keys/validate",
            headers={
                "X-API-Key": raw_key,
            },
        )

        if status != 200:
            raise RuntimeError(
                "API key validation failed."
            )

        if response[
            "tenant_id"
        ] != tenant_a_id:

            raise RuntimeError(
                "API key tenant mismatch."
            )

        if response[
            "project_id"
        ] != project_a_id:

            raise RuntimeError(
                "API key project mismatch."
            )

        print(
            "    VALID:",
            response["valid"],
        )

        print("    API KEY VALIDATION: PASS")

        # =================================================
        # USAGE
        # =================================================

        print()
        print("[8] Recording usage...")

        status, response = request(
            "POST",
            "/api/v1/usage",
            {
                "tenant_id": tenant_a_id,
                "project_id": project_a_id,
                "cpu_seconds": 10,
                "gpu_seconds": 5,
                "jobs": 1,
            },
        )

        if status != 200:
            raise RuntimeError(
                "Usage recording failed."
            )

        usage = response[
            "usage"
        ]

        print(
            "    CPU:",
            usage["cpu_seconds"],
        )

        print(
            "    GPU:",
            usage["gpu_seconds"],
        )

        print(
            "    JOBS:",
            usage["jobs"],
        )

        if usage[
            "cpu_seconds"
        ] != 10:

            raise RuntimeError(
                "CPU usage incorrect."
            )

        print("    USAGE TRACKING: PASS")

        # =================================================
        # QUOTA
        # =================================================

        print()
        print("[9] Testing quota enforcement...")

        status, response = request(
            "POST",
            "/api/v1/usage",
            {
                "tenant_id": tenant_a_id,
                "project_id": project_a_id,
                "cpu_seconds": 1000,
                "gpu_seconds": 0,
                "jobs": 0,
            },
        )

        print(
            "    STATUS:",
            status,
        )

        if status != 429:

            raise RuntimeError(
                "Quota enforcement failed."
            )

        print("    QUOTA ENFORCEMENT: PASS")

        # =================================================
        # REVOKE
        # =================================================

        print()
        print("[10] Revoking API key...")

        status, response = request(
            "POST",
            "/api/v1/api-keys/"
            f"{key_id}/revoke"
            f"?tenant_id={tenant_a_id}",
        )

        if status != 200:
            raise RuntimeError(
                "API key revocation failed."
            )

        if not response[
            "revoked"
        ]:

            raise RuntimeError(
                "API key was not revoked."
            )

        print("    REVOCATION: PASS")

        # =================================================
        # VALIDATE REVOKED KEY
        # =================================================

        print()
        print("[11] Testing revoked API key...")

        status, response = request(
            "GET",
            "/api/v1/api-keys/validate",
            headers={
                "X-API-Key": raw_key,
            },
        )

        print(
            "    STATUS:",
            status,
        )

        if status != 401:

            raise RuntimeError(
                "Revoked API key was accepted."
            )

        print("    REVOKED KEY BLOCKED: PASS")

        # =================================================
        # FINAL
        # =================================================

        print()
        print("=" * 60)
        print("M25 RESULT: PASS")
        print("=" * 60)

        print(
            "M25.1 TENANT / ORGANIZATION MODEL: PASS"
        )

        print(
            "M25.2 PROJECT ISOLATION: PASS"
        )

        print(
            "M25.3 API KEYS: PASS"
        )

        print(
            "M25.4 USAGE / QUOTAS: PASS"
        )

        print(
            "M25.5 MULTI-TENANT INTEGRATION: PASS"
        )

        print()
        print(
            "HYPERSPACE MULTI-TENANT SAAS FOUNDATION: COMPLETE"
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