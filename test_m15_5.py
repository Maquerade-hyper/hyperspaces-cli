from fastapi.testclient import TestClient

from apps.control_plane.main import app


client = TestClient(app)


# ---------------------------------------------------------
# CONTROLLER
# ---------------------------------------------------------

response = client.get("/")

assert response.status_code == 200

data = response.json()

assert data["service"] == "hyperspace-controller"
assert data["status"] == "online"

print("CONTROLLER: True")


# ---------------------------------------------------------
# HEALTH
# ---------------------------------------------------------

response = client.get("/health")

assert response.status_code == 200
assert response.json()["status"] == "healthy"

print("HEALTH: True")


# ---------------------------------------------------------
# NODE API
# ---------------------------------------------------------

response = client.get("/api/nodes")

assert response.status_code == 200

data = response.json()

assert "count" in data
assert "nodes" in data

print("NODES: True")


# ---------------------------------------------------------
# RESOURCE API
# ---------------------------------------------------------

response = client.get("/api/resources")

assert response.status_code == 200

data = response.json()

assert "count" in data
assert "resources" in data

print("RESOURCES: True")


# ---------------------------------------------------------
# AVAILABLE RESOURCES
# ---------------------------------------------------------

response = client.get(
    "/api/resources/available"
)

assert response.status_code == 200

print("AVAILABLE RESOURCES: True")


# ---------------------------------------------------------
# CLUSTER RESOURCES
# ---------------------------------------------------------

response = client.get(
    "/api/resources/cluster"
)

assert response.status_code == 200

print("CLUSTER RESOURCES: True")


# ---------------------------------------------------------
# JOB API
# ---------------------------------------------------------

response = client.get(
    "/api/jobs"
)

assert response.status_code == 200

data = response.json()

assert "count" in data
assert "jobs" in data

print("JOB LIST: True")


# ---------------------------------------------------------
# INVALID JOB
# ---------------------------------------------------------

response = client.get(
    "/api/jobs/M15-NONEXISTENT-JOB"
)

assert response.status_code == 404

print("JOB 404: True")


# ---------------------------------------------------------
# SCHEDULER API
# ---------------------------------------------------------

response = client.post(
    "/api/scheduler/assign",
    json={},
)

assert response.status_code != 404

print("SCHEDULER: True")


# ---------------------------------------------------------
# EXECUTION API
# ---------------------------------------------------------

response = client.post(
    "/api/execution",
    json={},
)

assert response.status_code != 404

print("EXECUTION: True")


# ---------------------------------------------------------
# DISTRIBUTED EXECUTION API
# ---------------------------------------------------------

response = client.post(
    "/api/execution/distributed",
    json={},
)

assert response.status_code != 404

print("DISTRIBUTED EXECUTION: True")


# ---------------------------------------------------------
# API DISCOVERY
# ---------------------------------------------------------

response = client.get(
    "/api"
)

assert response.status_code == 200

data = response.json()

assert data["service"] == "hyperspace-controller"
assert data["version"] == "0.4.0"

assert "nodes" in data["endpoints"]
assert "resources" in data["endpoints"]
assert "jobs" in data["endpoints"]
assert "scheduler" in data["endpoints"]
assert "execution" in data["endpoints"]

print("API DISCOVERY: True")


# ---------------------------------------------------------
# FASTAPI ROUTE COUNT
# ---------------------------------------------------------

routes = [
    route.path
    for route in app.routes
]

required_routes = [
    "/",
    "/health",
    "/api",
    "/api/nodes",
    "/api/nodes/{node_id}",
    "/api/resources",
    "/api/resources/available",
    "/api/resources/cluster",
    "/api/jobs",
    "/api/jobs/{job_id}",
    "/api/jobs/{job_id}/cancel",
    "/api/scheduler/assign",
    "/api/execution",
    "/api/execution/distributed",
]

for route in required_routes:
    assert route in routes

print("REQUIRED ROUTES: True")


# ---------------------------------------------------------
# FINAL
# ---------------------------------------------------------

print(
    "=== M15.5 CONTROLLER API INTEGRATION PASS ==="
)