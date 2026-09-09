from fastapi.testclient import TestClient

from apps.control_plane.main import app


client = TestClient(app)


# ---------------------------------------------------------
# ROOT
# ---------------------------------------------------------

response = client.get("/")

assert response.status_code == 200

data = response.json()

assert data["service"] == "hyperspace-controller"
assert data["version"] == "0.3.0"

print(
    "CONTROLLER API: True"
)


# ---------------------------------------------------------
# JOB LIST
# ---------------------------------------------------------

response = client.get(
    "/api/jobs"
)

assert response.status_code == 200

data = response.json()

assert "count" in data
assert "jobs" in data
assert isinstance(
    data["jobs"],
    list,
)

print(
    "JOB LIST API: True"
)


# ---------------------------------------------------------
# NODE API
# ---------------------------------------------------------

response = client.get(
    "/api/nodes"
)

assert response.status_code == 200

print(
    "NODE API: True"
)


# ---------------------------------------------------------
# RESOURCE API
# ---------------------------------------------------------

response = client.get(
    "/api/resources/cluster"
)

assert response.status_code == 200

print(
    "RESOURCE API: True"
)


# ---------------------------------------------------------
# INVALID JOB
# ---------------------------------------------------------

response = client.get(
    "/api/jobs/DOES-NOT-EXIST"
)

assert response.status_code == 404

print(
    "JOB 404 HANDLING: True"
)


# ---------------------------------------------------------
# SCHEDULER ENDPOINT EXISTS
# ---------------------------------------------------------

response = client.post(
    "/api/scheduler/assign",
    json={},
)

# The important part at this stage is that the route
# exists and is handled by the controller.
assert response.status_code != 404

print(
    "SCHEDULER API: True"
)


print(
    "=== M15.3 JOB & SCHEDULER API PASS ==="
)