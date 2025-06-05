import json
import unittest
from typing import Dict, List
from unittest.mock import MagicMock, patch

from cpln.errors import (
    WebSocketConnectionError,
    WebSocketExitCodeError,
    WebSocketOperationError,
)
from cpln.utils.websocket import WebSocketAPI


class TestWebSocketAPI(unittest.TestCase):
    def setUp(self) -> None:
        self.remote_wss: str = "wss://test.example.com"
        self.ws_api: WebSocketAPI = WebSocketAPI(self.remote_wss)
        self.mock_ws: MagicMock = MagicMock()

    # @patch('websocket.WebSocketApp')
    # def test_websocket_initialization(self, mock_ws_app):
    #     """Test that WebSocketApp is initialized correctly"""
    #     self.ws_api.websocket()
    #     mock_ws_app.assert_called_once_with(
    #         self.remote_wss,
    #         on_message=self.ws_api._on_message,
    #         on_error=self.ws_api._on_error,
    #         on_close=self.ws_api._on_close,
    #         on_open=self.ws_api._on_open,
    #     )

    def test_on_open_success(self) -> None:
        """Test successful connection opening"""
        request: Dict[str, str] = {"command": "test"}
        self.ws_api._request = request
        self.ws_api._on_open(self.mock_ws)
        self.mock_ws.send.assert_called_once_with(json.dumps(request, indent=4))

    def test_on_open_error(self) -> None:
        """Test error during connection opening"""
        self.ws_api._request: Dict[str, str] = {"command": "test"}
        self.mock_ws.send.side_effect = Exception("Connection error")
        self.ws_api._on_open(self.mock_ws)
        self.assertIsInstance(self.ws_api._error, WebSocketConnectionError)

    def test_on_message_success(self) -> None:
        """Test successful message processing"""
        message: bytes = b"Test message"
        self.ws_api._on_message(self.mock_ws, message)
        self.assertIsNone(self.ws_api._error)

    def test_on_message_exit_code_error(self) -> None:
        """Test handling of exit code errors"""
        message: bytes = b"exit code 1"
        self.ws_api._request: Dict[str, List[str]] = {"command": ["aws"]}
        self.ws_api._on_message(self.mock_ws, message)
        self.assertIsInstance(self.ws_api._error, WebSocketExitCodeError)

    def test_on_message_operation_error(self) -> None:
        """Test handling of operation errors"""
        message: bytes = b"error: something went wrong"
        self.ws_api._on_message(self.mock_ws, message)
        self.assertIsInstance(self.ws_api._error, WebSocketOperationError)

    def test_on_error(self) -> None:
        """Test error handling"""
        error: str = "Connection failed"
        self.ws_api._on_error(self.mock_ws, error)
        self.assertIsInstance(self.ws_api._error, WebSocketConnectionError)
        self.assertIn(error, str(self.ws_api._error))

    def test_on_close_normal(self) -> None:
        """Test normal connection closure"""
        self.ws_api._on_close(self.mock_ws, 1000, "Normal closure")
        self.assertIsNone(self.ws_api._error)

    def test_on_close_unexpected(self) -> None:
        """Test unexpected connection closure"""
        self.ws_api._on_close(self.mock_ws, 1006, "Abnormal closure")
        self.assertIsInstance(self.ws_api._error, WebSocketConnectionError)

    # @patch('websocket.WebSocketApp')
    # def test_exec_success(self, mock_ws_app):
    #     """Test successful execution"""
    #     mock_ws_instance = MagicMock()
    #     mock_ws_app.return_value = mock_ws_instance
    #     request = {"command": "echo hello world"}
    #     result = self.ws_api.exec(**request)
    #     self.assertEqual(result, request)
    #     mock_ws_instance.run_forever.assert_called_once()

    @patch("websocket.WebSocketApp")
    def test_exec_error(self, mock_ws_app: patch) -> None:
        """Test execution with error"""
        mock_ws_instance: MagicMock = MagicMock()
        mock_ws_app.return_value = mock_ws_instance
        self.ws_api._error = WebSocketConnectionError("Test error")

        with self.assertRaises(WebSocketConnectionError):
            self.ws_api.exec(command="test")


if __name__ == "__main__":
    unittest.main()
