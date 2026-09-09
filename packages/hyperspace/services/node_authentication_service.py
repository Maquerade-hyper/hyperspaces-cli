from hashlib import sha256

from hyperspace.core.models import SecurityIdentity


class NodeAuthenticationService:

    def __init__(self):
        self._trusted: dict[str, str] = {}

    def register(
        self,
        identity: SecurityIdentity,
    ) -> None:

        self._trusted[
            identity.node_id
        ] = identity.fingerprint

    def is_trusted(
        self,
        node_id: str,
        fingerprint: str,
    ) -> bool:

        trusted = self._trusted.get(
            node_id
        )

        return (
            trusted is not None
            and trusted == fingerprint
        )

    def authenticate(
        self,
        identity: SecurityIdentity,
    ) -> bool:

        return self.is_trusted(
            identity.node_id,
            identity.fingerprint,
        )

    def create_proof(
        self,
        identity: SecurityIdentity,
        challenge: str,
    ) -> str:

        data = (
            identity.private_key
            + challenge
        )

        return sha256(
            data.encode("utf-8")
        ).hexdigest()

    def verify_proof(
        self,
        identity: SecurityIdentity,
        challenge: str,
        proof: str,
    ) -> bool:

        expected = self.create_proof(
            identity,
            challenge,
        )

        return expected == proof

    def revoke(
        self,
        node_id: str,
    ) -> bool:

        return (
            self._trusted.pop(
                node_id,
                None,
            )
            is not None
        )

    def trusted_nodes(self) -> list[str]:

        return list(
            self._trusted.keys()
        )

    def clear(self) -> None:

        self._trusted.clear()