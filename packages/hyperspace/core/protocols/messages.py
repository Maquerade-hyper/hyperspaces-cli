from pydantic import BaseModel


class NodeHandshake(BaseModel):
    message_type: str = "node_handshake"
    node_id: str
    hostname: str
    platform: str
    ip_address: str
    port: int


class HandshakeAck(BaseModel):
    message_type: str = "handshake_ack"
    status: str
    node_id: str


class MeshJoinRequest(BaseModel):
    message_type: str = "mesh_join_request"
    token: str
    node_id: str
    hostname: str
    platform: str
    ip_address: str
    port: int


class MeshJoinResponse(BaseModel):
    message_type: str = "mesh_join_response"
    accepted: bool
    status: str | None = None
    mesh_id: str | None = None
    reason: str | None = None



class ResourceSnapshotMessage(BaseModel):
    message_type: str = "resource_snapshot"

    node_id: str

    mesh_id: str

    resources: dict


class ResourceSnapshotResponse(BaseModel):
    message_type: str = "resource_snapshot_response"

    accepted: bool

    node_id: str | None = None

    reason: str | None = None



class JobSubmitMessage(BaseModel):
    message_type: str = "job_submit"
    job: dict


class JobSubmitResponse(BaseModel):
    message_type: str = "job_submit_response"
    accepted: bool
    job_id: str | None = None
    status: str | None = None
    reason: str | None = None




class ExecutionRequestMessage(BaseModel):
    message_type: str = "execution_request"
    request: dict


class ExecutionResultMessage(BaseModel):
    message_type: str = "execution_result"
    result: dict


class ResultRequestMessage(BaseModel):
    message_type: str = "result_request"
    execution_id: str


class ResultResponseMessage(BaseModel):
    message_type: str = "result_response"
    found: bool
    result: dict | None = None