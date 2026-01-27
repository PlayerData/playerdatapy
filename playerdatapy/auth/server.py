import threading
import queue
from http.server import HTTPServer

from .callback_handler import CallbackHandler


class Server:
    """Manages the local HTTP server for OAuth callbacks."""

    def __init__(self, port):
        self.port = port
        self.server = None
        self.server_thread = None
        self.data_queue = queue.Queue()
        self.event = threading.Event()

    def create_handler(self, *args, **kwargs) -> "CallbackHandler":
        return CallbackHandler(self.data_queue, self.event, *args, **kwargs)

    def start(self):
        """Start the Oauth callback server."""

        self.server = HTTPServer(("localhost", self.port), self.create_handler)

        self.server_thread = threading.Thread(
            name="oauth_callback_server", target=self._serve_forever, daemon=True
        )
        self.server_thread.start()

    def _serve_forever(self):
        if self.server:
            self.server.serve_forever()

    def wait_for_callback(self):
        self.event.wait()
        return self.data_queue.get()

    def stop(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
