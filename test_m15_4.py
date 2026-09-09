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
assert data["version"] == "0.4.0"

print(
    "CONTROLLER API: True"
)


# ---------------------------------------------------------
# EXECUTION API
# ---------------------------------------------------------

response = client.post(
    "/api/execution",
    json={},
)

# Route must exist.
assert response.status_code != 404

print(
    "EXECUTION API: True"
)


# ---------------------------------------------------------
# DISTRIBUTED EXECUTION API
# ---------------------------------------------------------

response = client.post(
    "/api/execution/distributed",
    json={},
)

# Route must exist.
assert response.status_code != 404

print(
    "DISTRIBUTED EXECUTION API: True"
)


# ---------------------------------------------------------
# JOB API STILL EXISTS
# ---------------------------------------------------------

response = client.get(
    "/api/jobs"
)

assert response.status_code == 200

print(
    "JOB API: True"
)


# ---------------------------------------------------------
# RESOURCE API STILL EXISTS
# ---------------------------------------------------------

response = client.get(
    "/api/resources/cluster"
)

assert response.status_code == 200

print(
    "RESOURCE API: True"
)


# ---------------------------------------------------------
# API DISCOVERY
# ---------------------------------------------------------

response = client.get(
    "/api"
)

assert response.status_code == 200

data = response.json()

assert "endpoints" in data
assert "execution" in data["endpoints"]

print(
    "API DISCOVERY: True"
)


print(
    "=== M15.4 EXECUTION & RESULT API PASS ==="
)