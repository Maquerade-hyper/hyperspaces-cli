from pydantic import BaseModel


class MeshJoinRequest(BaseModel):
    message_type: str = "mesh_join_request"
    token: str
    node_id: str
    hostname: str
    platform: str
    ip_address: str
    port: int