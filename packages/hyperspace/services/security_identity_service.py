from hyperspace.core.models import SecurityIdentity
from hyperspace.services.node_identity_service import (
    NodeIdentityService,
)
from hyperspace.infrastructure.persistence.security_identity import (
    SecurityIdentityStore,
)


class SecurityIdentityService:

    def __init__(
        self,
        node_identity=None,
        store=None,
    ):
        self.node_identity = (
            node_identity
            or NodeIdentityService()
        )

        self.store = (
            store
            or SecurityIdentityStore()
        )

    def get_identity(self) -> SecurityIdentity:

        node = self.node_identity.get_node()

        data = self.store.get_or_create(
            node.node_id
        )

        return SecurityIdentity(
            node_id=data["node_id"],
            public_key=data["public_key"],
            private_key=data["private_key"],
            fingerprint=data["fingerprint"],
        )