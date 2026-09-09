from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from hyperspace.infrastructure.runtime import RuntimePaths


class CertificateService:

    def __init__(
        self,
        base_path: str | None = None,
    ):
        if base_path is None:
            base_path = str(RuntimePaths().certificates_dir)

        self.base_path = Path(base_path)

        self.ca_key = (
            self.base_path / "ca.key"
        )

        self.ca_cert = (
            self.base_path / "ca.crt"
        )

    def initialize(self) -> None:

        self.base_path.mkdir(
            parents=True,
            exist_ok=True,
        )

        if (
            self.ca_key.exists()
            and self.ca_cert.exists()
        ):
            return

        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,
        )

        subject = issuer = x509.Name(
            [
                x509.NameAttribute(
                    NameOID.COMMON_NAME,
                    "Hyperspace Mesh CA",
                )
            ]
        )

        now = datetime.now(timezone.utc)

        certificate = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(
                ca_certificate.subject
            )
            .public_key(
                node_private_key.public_key()
            )
            .serial_number(
                x509.random_serial_number()
            )
            .not_valid_before(
                now
            )
            .not_valid_after(
                now + timedelta(days=3650)
            )
            .add_extension(
                x509.BasicConstraints(
                    ca=False,
                    path_length=None,
                ),
                critical=True,
            )
            .add_extension(
                x509.SubjectAlternativeName(
                    [
                        x509.DNSName(
                            node_id
                        ),
                        x509.IPAddress(
                            __import__("ipaddress").ip_address(
                                "127.0.0.1"
                            )
                        ),
                    ]
                ),
                critical=False,
            )
            .sign(
                ca_private_key,
                hashes.SHA256(),
            )
        )

        self.ca_key.write_bytes(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )

        self.ca_cert.write_bytes(
            certificate.public_bytes(
                serialization.Encoding.PEM
            )
        )

    def create_node_certificate(
        self,
        node_id: str,
    ) -> tuple[Path, Path]:

        self.initialize()

        node_key = (
            self.base_path
            / f"{node_id}.key"
        )

        node_cert = (
            self.base_path
            / f"{node_id}.crt"
        )

        ca_private_key = serialization.load_pem_private_key(
            self.ca_key.read_bytes(),
            password=None,
        )

        ca_certificate = x509.load_pem_x509_certificate(
            self.ca_cert.read_bytes()
        )

        node_private_key = (
            rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )
        )

        subject = x509.Name(
            [
                x509.NameAttribute(
                    NameOID.COMMON_NAME,
                    node_id,
                )
            ]
        )

        now = datetime.now(timezone.utc)

        certificate = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(
                ca_certificate.subject
            )
            .public_key(
                node_private_key.public_key()
            )
            .serial_number(
                x509.random_serial_number()
            )
            .not_valid_before(
                now
            )
            .not_valid_after(
                now + timedelta(days=3650)
            )
            .add_extension(
                x509.BasicConstraints(
                    ca=False,
                    path_length=None,
                ),
                critical=True,
            )
            .sign(
                ca_private_key,
                hashes.SHA256(),
            )
        )

        node_key.write_bytes(
            node_private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )

        node_cert.write_bytes(
            certificate.public_bytes(
                serialization.Encoding.PEM
            )
        )

        return node_cert, node_key