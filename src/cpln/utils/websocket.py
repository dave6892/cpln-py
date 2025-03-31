import json
from websocket import WebSocketApp

class WebSocketAPI:

    def __init__(self, remote_wss: str):
        self.remote_wss = remote_wss

    def exec(self, **kwargs):
        self._request = kwargs
        ws = self.websocket()
        ws.run_forever()
        if ws.has_errored:
            raise Exception("Error in websocket connection")
        return self._request

    def websocket(self):
        ws = WebSocketApp(
            self.remote_wss,
            on_message = self._on_message,
            on_error = self._on_error,
            on_close = self._on_close,
            on_open = self._on_open,
        )
        return ws

    def _on_message(self, ws: WebSocketApp, message: str):
        print(f"Message from server: {message}")
        if "error" in message.decode():
            ws.sock.close()

    def _on_error(self, ws: WebSocketApp, error: str):
        print(f"Error: {error}")

    def _on_close(self, ws: WebSocketApp, close_status_code: int, close_msg: str):
        print(f"Connection closed, exit code: {close_status_code}")

    def _on_open(self, ws: WebSocketApp):
        print("Connection opened")
        # Establish a connection with the replica
        ws.send(json.dumps(self._request, indent=4))
