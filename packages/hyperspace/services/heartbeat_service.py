import threading
import time


class HeartbeatService:
    def __init__(self, interval: float = 10.0):
        self.interval = interval
        self.last_heartbeat = time.time()
        self._running = False
        self._thread = None

    def beat(self) -> float:
        self.last_heartbeat = time.time()
        return self.last_heartbeat

    def is_alive(self, timeout: float = 30.0) -> bool:
        return (time.time() - self.last_heartbeat) <= timeout

    def start(self) -> None:
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(
            target=self._heartbeat_loop,
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._running = False

    def _heartbeat_loop(self) -> None:
        while self._running:
            self.beat()
            time.sleep(self.interval)