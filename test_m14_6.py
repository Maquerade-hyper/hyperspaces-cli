from hyperspace.core.models import SecurityIdentity

from hyperspace.services import (
    Permission,
    Role,
    SecurityIntegrationService,
)

from hyperspace.infrastructure.networking.tcp_transport import (
    TCPTransport,
)


# ---------------------------------------------------------
# SECURITY SETUP
# ---------------------------------------------------------

security = SecurityIntegrationService()

controller_identity = SecurityIdentity(
    node_id="CONTROLLER-01",
    public_key="controller-public",
    private_key="controller-private",
    fingerprint="controller-fingerprint",
)

worker_identity = SecurityIdentity(
    node_id="WORKER-01",
    public_key="worker-public",
    private_key="worker-private",
    fingerprint="worker-fingerprint",
)

observer_identity = SecurityIdentity(
    node_id="OBSERVER-01",
    public_key="observer-public",
    private_key="observer-private",
    fingerprint="observer-fingerprint",
)


# ---------------------------------------------------------
# REGISTER NODES
# ---------------------------------------------------------

security.register_node(
    controller_identity,
    Role.CONTROLLER,
)

security.register_node(
    worker_identity,
    Role.WORKER,
)

security.register_node(
    observer_identity,
    Role.OBSERVER,
)


# ---------------------------------------------------------
# CREATE TRANSPORT
# ---------------------------------------------------------

transport = TCPTransport(
    security=security,
)


# ---------------------------------------------------------
# TEST AUTHENTICATION
# ---------------------------------------------------------

assert transport._authenticate_request(
    {
        "node_id": "WORKER-01",
        "fingerprint": "worker-fingerprint",
    }
) == "WORKER-01"

print(
    "WORKER AUTHENTICATION: True"
)


# ---------------------------------------------------------
# TEST CONTROLLER PERMISSIONS
# ---------------------------------------------------------

transport._authorize_request(
    {
        "node_id": "CONTROLLER-01",
        "fingerprint": "controller-fingerprint",
    },
    Permission.JOB_SUBMIT,
)

print(
    "CONTROLLER JOB SUBMIT: True"
)


# ---------------------------------------------------------
# TEST WORKER PERMISSIONS
# ---------------------------------------------------------

transport._authorize_request(
    {
        "node_id": "WORKER-01",
        "fingerprint": "worker-fingerprint",
    },
    Permission.JOB_EXECUTE,
)

print(
    "WORKER JOB EXECUTE: True"
)


# ---------------------------------------------------------
# WORKER MUST NOT SUBMIT JOBS
# ---------------------------------------------------------

worker_submit_rejected = False

try:

    transport._authorize_request(
        {
            "node_id": "WORKER-01",
            "fingerprint": "worker-fingerprint",
        },
        Permission.JOB_SUBMIT,
    )

except PermissionError:

    worker_submit_rejected = True


print(
    "WORKER JOB SUBMIT REJECTED:",
    worker_submit_rejected,
)

assert worker_submit_rejected is True


# ---------------------------------------------------------
# OBSERVER MUST NOT EXECUTE JOBS
# ---------------------------------------------------------

observer_execute_rejected = False

try:

    transport._authorize_request(
        {
            "node_id": "OBSERVER-01",
            "fingerprint": "observer-fingerprint",
        },
        Permission.JOB_EXECUTE,
    )

except PermissionError:

    observer_execute_rejected = True


print(
    "OBSERVER JOB EXECUTE REJECTED:",
    observer_execute_rejected,
)

assert observer_execute_rejected is True


# ---------------------------------------------------------
# BAD FINGERPRINT MUST BE REJECTED
# ---------------------------------------------------------

bad_fingerprint_rejected = False

try:

    transport._authenticate_request(
        {
            "node_id": "WORKER-01",
            "fingerprint": "WRONG-FINGERPRINT",
        }
    )

except PermissionError:

    bad_fingerprint_rejected = True


print(
    "BAD FINGERPRINT REJECTED:",
    bad_fingerprint_rejected,
)

assert bad_fingerprint_rejected is True


# ---------------------------------------------------------
# UNKNOWN NODE MUST BE REJECTED
# ---------------------------------------------------------

unknown_node_rejected = False

try:

    transport._authenticate_request(
        {
            "node_id": "UNKNOWN-01",
            "fingerprint": "unknown-fingerprint",
        }
    )

except PermissionError:

    unknown_node_rejected = True


print(
    "UNKNOWN NODE REJECTED:",
    unknown_node_rejected,
)

assert unknown_node_rejected is True


# ---------------------------------------------------------
# MISSING IDENTITY MUST BE REJECTED
# ---------------------------------------------------------

missing_identity_rejected = False

try:

    transport._authenticate_request(
        {
            "node_id": "WORKER-01",
        }
    )

except PermissionError:

    missing_identity_rejected = True


print(
    "MISSING FINGERPRINT REJECTED:",
    missing_identity_rejected,
)

assert missing_identity_rejected is True


# ---------------------------------------------------------
# REVOCATION
# ---------------------------------------------------------

security.revoke_node(
    "WORKER-01"
)

revoked_node_rejected = False

try:

    transport._authenticate_request(
        {
            "node_id": "WORKER-01",
            "fingerprint": "worker-fingerprint",
        }
    )

except PermissionError:

    revoked_node_rejected = True


print(
    "REVOKED NODE REJECTED:",
    revoked_node_rejected,
)

assert revoked_node_rejected is True


# ---------------------------------------------------------
# FINAL
# ---------------------------------------------------------

print(
    "=== M14.6 SECURITY INTEGRATION PASS ==="
)