import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs


class CallbackHandler(BaseHTTPRequestHandler):
    """Overwrite some methods of the BaseHTTPRequestHandler to handle oauth callback requests"""

    def __init__(self, data_queue, event, *args, **kwargs):
        self.data_queue = data_queue
        self.event = event
        super().__init__(*args, **kwargs)

    def do_GET(self):
        # Override the do_GET method to handle oauth callback requests
        try:
            query_components = self._parse_query_string()
            code = query_components.get("code")

            if not code or len(code) == 0:
                self._send_error_response()
                return

            self.data_queue.put(code[0])
            self.event.set()
            self._send_success_response()

        except Exception:
            self._send_error_response()

    def _parse_query_string(self) -> dict:
        return json.loads(str(parse_qs(urlparse(self.path).query)).replace("'", '"'))

    def _send_success_response(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(
            bytes("<p>Success! Please return to the terminal</p>", "utf-8")
        )

    def _send_error_response(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(
            bytes(
                "<p>There was a parsing error, please run your script again from the terminal</p>",
                "utf-8",
            )
        )

    def log_message(self, format, *args):
        # Override the log_message method to suppress server logs
        return
