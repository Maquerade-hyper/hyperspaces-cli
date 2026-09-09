from hyperspace.services.permission_service import (
    PermissionService,
    Permission,
    Role,
)


service = PermissionService()

service.assign_role(
    "NODE-A",
    Role.WORKER,
)

service.assign_role(
    "NODE-B",
    Role.OBSERVER,
)


print(
    "NODE-A ROLE:",
    service.get_role("NODE-A").value,
)

print(
    "WORKER EXECUTE:",
    service.has_permission(
        "NODE-A",
        Permission.JOB_EXECUTE,
    ),
)

print(
    "WORKER SUBMIT:",
    service.has_permission(
        "NODE-A",
        Permission.JOB_SUBMIT,
    ),
)

print(
    "OBSERVER READ:",
    service.has_permission(
        "NODE-B",
        Permission.JOB_READ,
    ),
)

print(
    "OBSERVER EXECUTE:",
    service.has_permission(
        "NODE-B",
        Permission.JOB_EXECUTE,
    ),
)

try:

    service.require(
        "NODE-B",
        Permission.JOB_EXECUTE,
    )

except PermissionError:

    print(
        "UNAUTHORIZED ACTION REJECTED: True"
    )


assert service.has_permission(
    "NODE-A",
    Permission.JOB_EXECUTE,
)

assert not service.has_permission(
    "NODE-A",
    Permission.JOB_SUBMIT,
)

assert service.has_permission(
    "NODE-B",
    Permission.JOB_READ,
)

assert not service.has_permission(
    "NODE-B",
    Permission.JOB_EXECUTE,
)

print(
    "=== M14.4 PERMISSION PASS ==="
)