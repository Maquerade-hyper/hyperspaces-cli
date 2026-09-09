from hyperspace.core.models import SecurityIdentity

from hyperspace.services import (
    Permission,
    Role,
    SecurityIntegrationService,
)


security = SecurityIntegrationService()

identity = SecurityIdentity(
    node_id="NODE-A",
    public_key="public-key",
    private_key="private-key",
    fingerprint="fingerprint-a",
)

security.register_node(
    identity,
    Role.WORKER,
)

print(
    "ROLE:",
    security.get_role("NODE-A").value,
)

print(
    "TRUSTED:",
    security.is_trusted(
        "NODE-A",
        "fingerprint-a",
    ),
)

print(
    "AUTHENTICATED:",
    security.authenticate_node(
        identity
    ),
)

print(
    "EXECUTE ALLOWED:",
    security.authorize(
        "NODE-A",
        Permission.JOB_EXECUTE,
    ),
)

print(
    "SUBMIT ALLOWED:",
    security.authorize(
        "NODE-A",
        Permission.JOB_SUBMIT,
    ),
)

try:

    security.require(
        "NODE-A",
        Permission.JOB_SUBMIT,
    )

    unauthorized_rejected = False

except PermissionError:

    unauthorized_rejected = True


print(
    "UNAUTHORIZED ACTION REJECTED:",
    unauthorized_rejected,
)

security.revoke_node("NODE-A")

print(
    "REVOKED TRUST:",
    not security.is_trusted(
        "NODE-A",
        "fingerprint-a",
    ),
)

print(
    "REVOKED ROLE:",
    security.get_role("NODE-A") is None,
)

print(
    "=== M14.5 SECURITY INTEGRATION PASS ==="
)