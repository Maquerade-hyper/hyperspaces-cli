import ssl
from pathlib import Path


class TLSConfig:

    def __init__(
        self,
        certificate_path: str,
        private_key_path: str,
        ca_certificate_path: str | None = None,
    ):
        self.certificate_path = Path(
            certificate_path
        )

        self.private_key_path = Path(
            private_key_path
        )

        self.ca_certificate_path = (
            Path(ca_certificate_path)
            if ca_certificate_path
            else None
        )

    def create_server_context(
        self,
    ) -> ssl.SSLContext:

        context = ssl.SSLContext(
            ssl.PROTOCOL_TLS_SERVER
        )

        context.minimum_version = (
            ssl.TLSVersion.TLSv1_2
        )

        context.load_cert_chain(
            certfile=str(
                self.certificate_path
            ),
            keyfile=str(
                self.private_key_path
            ),
        )

        if self.ca_certificate_path:

            context.verify_mode = (
                ssl.CERT_REQUIRED
            )

            context.load_verify_locations(
                cafile=str(
                    self.ca_certificate_path
                )
            )

        return context

    def create_client_context(
        self,
    ) -> ssl.SSLContext:

        context = ssl.SSLContext(
            ssl.PROTOCOL_TLS_CLIENT
        )

        context.minimum_version = (
            ssl.TLSVersion.TLSv1_2
        )

        if self.ca_certificate_path:

            context.load_verify_locations(
                cafile=str(
                    self.ca_certificate_path
                )
            )

            context.check_hostname = False

            context.verify_mode = (
                ssl.CERT_REQUIRED
            )

            # Present this node's certificate
            # to the TLS server.
            context.load_cert_chain(
                certfile=str(
                    self.certificate_path
                ),
                keyfile=str(
                    self.private_key_path
                ),
            )

        else:

            context.check_hostname = False

            context.verify_mode = (
                ssl.CERT_NONE
            )

        return context