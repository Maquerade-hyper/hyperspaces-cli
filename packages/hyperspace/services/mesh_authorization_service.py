from hyperspace.core.models import MeshMemberStatus
from hyperspace.services.mesh_membership_service import MeshMembershipService


class MeshAuthorizationService:
    def __init__(self, membership=None):
        self.membership = membership or MeshMembershipService()

    def is_member_approved(self, node_id: str) -> bool:
        member = self.membership.get(node_id)

        if member is None:
            return False

        return member.status == MeshMemberStatus.APPROVED

    def authorize_node(self, node_id: str) -> None:
        if not self.is_member_approved(node_id):
            raise PermissionError(
                "Node is not an approved mesh member."
            )

    def can_access_mesh_resources(
        self,
        node_id: str,
    ) -> bool:
        return self.is_member_approved(node_id)

    def can_access_controller_resources(
        self,
        node_id: str,
    ) -> bool:
        return False