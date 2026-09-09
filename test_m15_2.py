from fastapi.testclient import TestClient

from apps.control_plane.main import app


client = TestClient(app)


# ---------------------------------------------------------
# NODES
# ---------------------------------------------------------

response = client.get(
    "/api/nodes"
)

assert response.status_code == 200

data = response.json()

assert "count" in data
assert "nodes" in data
assert isinstance(data["nodes"], list)

print(
    "NODE LIST API: True"
)


# ---------------------------------------------------------
# RESOURCES
# ---------------------------------------------------------

response = client.get(
    "/api/resources"
)

assert response.status_code == 200

data = response.json()

assert "count" in data
assert "resources" in data
assert isinstance(data["resources"], list)

print(
    "RESOURCE LIST API: True"
)


# ---------------------------------------------------------
# AVAILABLE RESOURCES
# ---------------------------------------------------------

response = client.get(
    "/api/resources/available"
)

assert response.status_code == 200

print(
    "AVAILABLE RESOURCE API: True"
)


# ---------------------------------------------------------
# CLUSTER RESOURCES
# ---------------------------------------------------------

response = client.get(
    "/api/resources/cluster"
)

assert response.status_code == 200

print(
    "CLUSTER RESOURCE API: True"
)


# ---------------------------------------------------------
# VERSION
# ---------------------------------------------------------

response = client.get("/")

assert response.status_code == 200

assert response.json()["version"] == "0.2.0"

print(
    "API VERSION: True"
)


print(
    "=== M15.2 NODE & RESOURCE API PASS ==="
)