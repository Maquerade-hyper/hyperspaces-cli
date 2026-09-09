from hyperspace.services.mesh_controller_service import MeshControllerService
from hyperspace.services.mesh_invite_service import MeshInviteService
from hyperspace.services.mesh_membership_service import MeshMembershipService


class MeshJoinService:
    def __init__(
        self,
        controller=None,
        invites=None,
        membership=None,
    ):
        self.controller = controller or MeshControllerService()
        self.invites = invites or MeshInviteService(self.controller)
        self.membership = membership or MeshMembershipService()

    def process_join_request(self, request: dict) -> dict:
        token = request.get("token")

        if not token:
            return {
                "message_type": "mesh_join_response",
                "accepted": False,
                "reason": "Missing invite token.",
            }

        try:
            invite = self.invites.validate_invite(token)
        except ValueError as exc:
            return {
                "message_type": "mesh_join_response",
                "accepted": False,
                "reason": str(exc),
            }

        if invite["mesh_id"] != self.controller.get_mesh().mesh_id:
            return {
                "message_type": "mesh_join_response",
                "accepted": False,
                "reason": "Invite belongs to another mesh.",
            }

        member = self.membership.request_join(
            mesh_id=invite["mesh_id"],
            node_id=request["node_id"],
            hostname=request["hostname"],
            platform=request["platform"],
            ip_address=request["ip_address"],
            port=request["port"],
        )

        self.invites.consume_invite(token)

        return {
            "message_type": "mesh_join_response",
            "accepted": True,
            "status": member.status.value,
            "mesh_id": member.mesh_id,
            "reason": "Join request accepted and awaiting approval.",
        }