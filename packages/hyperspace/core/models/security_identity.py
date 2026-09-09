from pydantic import BaseModel


class SecurityIdentity(BaseModel):
    node_id: str
    public_key: str
    private_key: str
    fingerprint: str