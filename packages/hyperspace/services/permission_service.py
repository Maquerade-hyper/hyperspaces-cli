from enum import Enum


class Permission(str, Enum):

    NODE_DISCOVERY = "node_discovery"
    NODE_JOIN = "node_join"

    RESOURCE_READ = "resource_read"
    RESOURCE_USE = "resource_use"

    JOB_SUBMIT = "job_submit"
    JOB_EXECUTE = "job_execute"
    JOB_READ = "job_read"

    ARTIFACT_READ = "artifact_read"
    ARTIFACT_WRITE = "artifact_write"


class Role(str, Enum):

    CONTROLLER = "controller"
    WORKER = "worker"
    OBSERVER = "observer"


class PermissionService:

    ROLE_PERMISSIONS = {

        Role.CONTROLLER: {
            Permission.NODE_DISCOVERY,
            Permission.NODE_JOIN,
            Permission.RESOURCE_READ,
            Permission.RESOURCE_USE,
            Permission.JOB_SUBMIT,
            Permission.JOB_EXECUTE,
            Permission.JOB_READ,
            Permission.ARTIFACT_READ,
            Permission.ARTIFACT_WRITE,
        },

        Role.WORKER: {
            Permission.NODE_DISCOVERY,
            Permission.RESOURCE_READ,
            Permission.RESOURCE_USE,
            Permission.JOB_EXECUTE,
            Permission.JOB_READ,
            Permission.ARTIFACT_READ,
            Permission.ARTIFACT_WRITE,
        },

        Role.OBSERVER: {
            Permission.NODE_DISCOVERY,
            Permission.RESOURCE_READ,
            Permission.JOB_READ,
            Permission.ARTIFACT_READ,
        },
    }

    def __init__(self):

        self._roles: dict[
            str,
            Role,
        ] = {}

    def assign_role(
        self,
        node_id: str,
        role: Role,
    ) -> None:

        self._roles[node_id] = role

    def remove_role(
        self,
        node_id: str,
    ) -> bool:

        return (
            self._roles.pop(
                node_id,
                None,
            )
            is not None
        )

    def get_role(
        self,
        node_id: str,
    ) -> Role | None:

        return self._roles.get(
            node_id
        )

    def has_permission(
        self,
        node_id: str,
        permission: Permission,
    ) -> bool:

        role = self._roles.get(
            node_id
        )

        if role is None:
            return False

        return permission in (
            self.ROLE_PERMISSIONS[
                role
            ]
        )

    def require(
        self,
        node_id: str,
        permission: Permission,
    ) -> None:

        if not self.has_permission(
            node_id,
            permission,
        ):

            raise PermissionError(
                f"Node '{node_id}' "
                f"does not have permission "
                f"'{permission.value}'."
            )

    def list_permissions(
        self,
        node_id: str,
    ) -> list[Permission]:

        role = self._roles.get(
            node_id
        )

        if role is None:
            return []

        return list(
            self.ROLE_PERMISSIONS[
                role
            ]
        )

    def clear(self) -> None:

        self._roles.clear()