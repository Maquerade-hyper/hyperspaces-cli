import socket


class NetworkDiscovery:
    def hostname(self) -> str:
        return socket.gethostname()

    def local_ip(self) -> str:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        try:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
        finally:
            sock.close()