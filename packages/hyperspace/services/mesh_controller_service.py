from hyperspace.core.models import Mesh
from hyperspace.services.mesh_storage_service import MeshStorageService
from hyperspace.services.node_identity_service import NodeIdentityService


class MeshControllerService:
    def __init__(self):
        self.node_identity = NodeIdentityService()
        self.storage = MeshStorageService()
        self._mesh: Mesh | None = self.storage.load()

    def create_mesh(self, name: str) -> Mesh:
        if self._mesh is not None:
            raise ValueError(
                "A mesh already exists on this controller."
            )

        node = self.node_identity.get_node()

        self._mesh = Mesh(
            name=name,
            owner_node_id=node.node_id,
        )

        self.storage.save(self._mesh)

        return self._mesh

    def get_mesh(self) -> Mesh | None:
        return self._mesh

    def mesh_exists(self) -> bool:
        return self._mesh is not None

    def status(self) -> dict:
        if self._mesh is None:
            return {
                "mesh_exists": False,
                "status": "no_mesh",
            }

        return {
            "mesh_exists": True,
            "mesh_id": self._mesh.mesh_id,
            "name": self._mesh.name,
            "owner_node_id": self._mesh.owner_node_id,
            "status": self._mesh.status.value,
        }