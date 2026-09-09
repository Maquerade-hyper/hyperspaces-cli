from hyperspace.core.models import SecurityIdentity
from hyperspace.services.node_authentication_service import (
    NodeAuthenticationService,
)
from hyperspace.services.permission_service import (
    Permission,
    PermissionService,
    Role,
)


class SecurityIntegrationService:

    def __init__(
        self,
        authentication=None,
        permissions=None,
    ):
        self.authentication = (
            authentication
            or NodeAuthenticationService()
        )

        self.permissions = (
            permissions
            or PermissionService()
        )

    def register_node(
        self,
        identity: SecurityIdentity,
        role: Role,
    ) -> None:

        self.authentication.register(identity)

        self.permissions.assign_role(
            identity.node_id,
            role,
        )

    def authenticate_node(
        self,
        identity: SecurityIdentity,
    ) -> bool:

        return self.authentication.authenticate(
            identity
        )

    def authorize(
        self,
        node_id: str,
        permission: Permission,
    ) -> bool:

        return self.permissions.has_permission(
            node_id,
            permission,
        )

    def require(
        self,
        node_id: str,
        permission: Permission,
    ) -> None:

        self.permissions.require(
            node_id,
            permission,
        )

    def get_role(
        self,
        node_id: str,
    ) -> Role | None:

        return self.permissions.get_role(
            node_id
        )

    def revoke_node(
        self,
        node_id: str,
    ) -> bool:

        revoked = self.authentication.revoke(
            node_id
        )

        self.permissions.remove_role(
            node_id
        )

        return revoked

    def is_trusted(
        self,
        node_id: str,
        fingerprint: str,
    ) -> bool:

        return self.authentication.is_trusted(
            node_id,
            fingerprint,
        )

    def clear(self) -> None:

        self.authentication.clear()
        self.permissions.clear()