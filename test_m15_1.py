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
assert data["status"] == "online"
assert data["version"] == "0.1.0"

print(
    "ROOT ENDPOINT: True"
)


# ---------------------------------------------------------
# HEALTH
# ---------------------------------------------------------

response = client.get("/health")

assert response.status_code == 200

data = response.json()

assert data["status"] == "healthy"

print(
    "HEALTH ENDPOINT: True"
)


# ---------------------------------------------------------
# API APPLICATION
# ---------------------------------------------------------

assert app.title == "Hyperspace Controller API"

print(
    "API APPLICATION: True"
)


print(
    "=== M15.1 CONTROLLER API FOUNDATION PASS ==="
)