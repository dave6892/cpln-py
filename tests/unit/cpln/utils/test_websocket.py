"""Tests for WebSocket API following unit testing best practices."""

import json
import unittest
from unittest.mock import MagicMock, patch

from cpln.errors import (
    WebSocketConnectionError,
    WebSocketExitCodeError,
    WebSocketOperationError,
)
from cpln.utils.websocket import WebSocketAPI


class TestWebSocketAPIInitialization(unittest.TestCase):
    """Test WebSocketAPI initialization and basic configuration"""

    def test_websocket_api_initialization_with_default_verbose_creates_instance(self):
        """Test that WebSocketAPI initializes correctly with default verbose setting"""
        remote_wss = "wss://test.example.com"

        ws_api = WebSocketAPI(remote_wss)

        self.assertEqual(ws_api.remote_wss, remote_wss)
        self.assertFalse(ws_api.verbose)
        self.assertIsNone(ws_api._request)
        self.assertIsNone(ws_api._error)

    def test_websocket_api_initialization_with_verbose_enabled_sets_flag(self):
        """Test that WebSocketAPI initializes correctly with verbose enabled"""
        remote_wss = "wss://verbose.example.com"
        verbose = True

        ws_api = WebSocketAPI(remote_wss, verbose=verbose)

        self.assertTrue(ws_api.verbose)

    def test_websocket_api_initialization_with_complex_url_parses_correctly(self):
        """Test that WebSocketAPI handles complex URLs with parameters"""
        remote_wss = "wss://api.cpln.io/v1/ws?token=abc123&org=myorg&gvc=mygvc"

        ws_api = WebSocketAPI(remote_wss)

        self.assertEqual(ws_api.remote_wss, remote_wss)


class TestWebSocketConnection(unittest.TestCase):
    """Test WebSocket connection creation and configuration"""

    def setUp(self):
        """Set up common test fixtures"""
        self.remote_wss = "wss://test.example.com"
        self.ws_api = WebSocketAPI(self.remote_wss)

    @patch("cpln.utils.websocket.WebSocketApp")
    def test_websocket_creation_configures_all_handlers(self, mock_websocket_app):
        """Test that websocket() creates WebSocketApp with all required handlers"""
        mock_ws_instance = MagicMock()
        mock_websocket_app.return_value = mock_ws_instance

        result = self.ws_api.websocket()

        mock_websocket_app.assert_called_once_with(
            self.remote_wss,
            on_message=self.ws_api._on_message,
            on_error=self.ws_api._on_error,
            on_close=self.ws_api._on_close,
            on_open=self.ws_api._on_open,
        )
        self.assertEqual(result, mock_ws_instance)

    @patch("cpln.utils.websocket.WebSocketApp")
    def test_websocket_creation_returns_configured_instance(self, mock_websocket_app):
        """Test that websocket() returns the configured WebSocketApp instance"""
        mock_ws_instance = MagicMock()
        mock_websocket_app.return_value = mock_ws_instance

        result = self.ws_api.websocket()

        self.assertIs(result, mock_ws_instance)


class TestConnectionHandlers(unittest.TestCase):
    """Test WebSocket connection event handlers"""

    def setUp(self):
        """Set up common test fixtures"""
        self.remote_wss = "wss://test.example.com"
        self.ws_api = WebSocketAPI(self.remote_wss)
        self.mock_ws = MagicMock()

    def test_on_open_with_valid_request_sends_json_message(self):
        """Test that _on_open sends the request as JSON when connection opens"""
        request = {"command": "echo test", "token": "abc123"}
        self.ws_api._request = request  # type: ignore
        expected_json = json.dumps(request, indent=4)

        self.ws_api._on_open(self.mock_ws)

        self.mock_ws.send.assert_called_once_with(expected_json)
        self.assertIsNone(self.ws_api._error)

    def test_on_open_with_send_exception_sets_connection_error(self):
        """Test that _on_open handles send exceptions gracefully"""
        request = {"command": "test"}
        self.ws_api._request = request  # type: ignore
        send_error = Exception("Network error")
        self.mock_ws.send.side_effect = send_error

        self.ws_api._on_open(self.mock_ws)

        self.assertIsInstance(self.ws_api._error, WebSocketConnectionError)
        self.assertIn("Error sending initial request", str(self.ws_api._error))
        self.assertIn("Network error", str(self.ws_api._error))
        self.mock_ws.sock.close.assert_called_once()

    def test_on_open_with_verbose_enabled_prints_connection_message(self):
        """Test that _on_open prints connection message when verbose is enabled"""
        self.ws_api.verbose = True
        self.ws_api._request = {"command": "test"}  # type: ignore

        with patch("builtins.print") as mock_print:
            self.ws_api._on_open(self.mock_ws)

            mock_print.assert_called_with("Connection opened")

    def test_on_close_with_normal_closure_code_does_not_set_error(self):
        """Test that _on_close does not set error for normal closure (code 1000)"""
        self.ws_api._on_close(self.mock_ws, 1000, "Normal closure")

        self.assertIsNone(self.ws_api._error)

    def test_on_close_with_none_status_code_does_not_set_error(self):
        """Test that _on_close does not set error when status code is None"""
        self.ws_api._on_close(self.mock_ws, None, "Clean closure")  # type: ignore

        self.assertIsNone(self.ws_api._error)

    def test_on_close_with_abnormal_closure_code_sets_connection_error(self):
        """Test that _on_close sets connection error for abnormal closure codes"""
        close_code = 1006
        close_message = "Abnormal closure"

        self.ws_api._on_close(self.mock_ws, close_code, close_message)

        self.assertIsInstance(self.ws_api._error, WebSocketConnectionError)
        self.assertIn("Connection closed unexpectedly", str(self.ws_api._error))
        self.assertIn(str(close_code), str(self.ws_api._error))
        self.assertIn(close_message, str(self.ws_api._error))

    def test_on_close_with_verbose_enabled_prints_closure_message(self):
        """Test that _on_close prints closure message when verbose is enabled"""
        self.ws_api.verbose = True
        close_code = 1000

        with patch("builtins.print") as mock_print:
            self.ws_api._on_close(self.mock_ws, close_code, "Normal closure")

            mock_print.assert_called_with(f"Connection closed, exit code: {close_code}")

    def test_on_error_sets_websocket_connection_error_with_message(self):
        """Test that _on_error sets WebSocketConnectionError with provided error message"""
        error_message = "Connection timeout"

        self.ws_api._on_error(self.mock_ws, error_message)

        self.assertIsInstance(self.ws_api._error, WebSocketConnectionError)
        self.assertIn("WebSocket error", str(self.ws_api._error))
        self.assertIn(error_message, str(self.ws_api._error))


class TestMessageProcessing(unittest.TestCase):
    """Test WebSocket message processing with various scenarios"""

    def setUp(self):
        """Set up common test fixtures"""
        self.remote_wss = "wss://test.example.com"
        self.ws_api = WebSocketAPI(self.remote_wss)
        self.mock_ws = MagicMock()

    def _create_mock_message(self, content: str):
        """Helper method to create mock messages that have a decode method"""

        # Create a mock object that has a decode method returning the content
        class MockMessage:
            def __init__(self, decoded_content: str):
                self._decoded_content = decoded_content

            def decode(self) -> str:
                return self._decoded_content

        return MockMessage(content)

    def test_on_message_with_successful_output_processes_without_error(self):
        """Test that _on_message processes successful command output without setting error"""
        message = self._create_mock_message("Command executed successfully")

        with patch("builtins.print") as mock_print:
            result = self.ws_api._on_message(self.mock_ws, message)  # type: ignore

            self.assertIsNone(self.ws_api._error)
            self.assertEqual(result, 0)  # Default exit code
            mock_print.assert_called_once_with("Command executed successfully")

    def test_on_message_with_zero_exit_code_processes_normally(self):
        """Test that _on_message processes messages with explicit zero exit code"""
        message = self._create_mock_message("Process completed exit code 0")

        with patch("builtins.print") as mock_print:
            result = self.ws_api._on_message(self.mock_ws, message)  # type: ignore

            self.assertIsNone(self.ws_api._error)
            self.assertEqual(result, 0)
            mock_print.assert_called_once_with("Process completed exit code 0")

    def test_on_message_with_error_keyword_sets_operation_error(self):
        """Test that _on_message sets WebSocketOperationError when message contains 'error'"""
        error_message = "Error: Unable to connect to database"
        message = self._create_mock_message(error_message)

        self.ws_api._on_message(self.mock_ws, message)  # type: ignore

        self.assertIsInstance(self.ws_api._error, WebSocketOperationError)
        self.assertIn("Error in message", str(self.ws_api._error))
        self.assertIn(error_message, str(self.ws_api._error))

    def test_on_message_with_failed_keyword_sets_operation_error(self):
        """Test that _on_message sets WebSocketOperationError when message contains 'failed'"""
        failure_message = "Operation failed: timeout occurred"
        message = self._create_mock_message(failure_message)

        self.ws_api._on_message(self.mock_ws, message)  # type: ignore

        self.assertIsInstance(self.ws_api._error, WebSocketOperationError)
        self.assertIn("Operation failed", str(self.ws_api._error))
        self.assertIn(failure_message, str(self.ws_api._error))

    def test_on_message_with_case_insensitive_error_detection_works(self):
        """Test that _on_message detects error keywords case-insensitively"""
        test_cases = [
            "ERROR: Something went wrong",
            "Error: Something went wrong",
            "error: Something went wrong",
            "FAILED to complete",
            "Failed to complete",
            "failed to complete",
        ]

        for error_message in test_cases:
            with self.subTest(error_message=error_message):
                self.ws_api._error = None  # Reset error state
                message = self._create_mock_message(error_message)

                self.ws_api._on_message(self.mock_ws, message)  # type: ignore

                self.assertIsInstance(self.ws_api._error, WebSocketOperationError)


class TestExitCodeHandling(unittest.TestCase):
    """Test WebSocket message processing with various exit codes"""

    def setUp(self):
        """Set up common test fixtures"""
        self.remote_wss = "wss://test.example.com"
        self.ws_api = WebSocketAPI(self.remote_wss)
        self.mock_ws = MagicMock()

    def _create_mock_message(self, content: str):
        """Helper method to create mock messages that have a decode method"""

        # Create a mock object that has a decode method returning the content
        class MockMessage:
            def __init__(self, decoded_content: str):
                self._decoded_content = decoded_content

            def decode(self) -> str:
                return self._decoded_content

        return MockMessage(content)

    def test_on_message_with_non_zero_exit_code_sets_exit_code_error(self):
        """Test that _on_message sets WebSocketExitCodeError for non-zero exit codes"""
        message = self._create_mock_message("Process failed exit code 1")
        self.ws_api._request = {"command": ["generic"]}  # type: ignore

        result = self.ws_api._on_message(self.mock_ws, message)  # type: ignore

        self.assertIsInstance(self.ws_api._error, WebSocketExitCodeError)
        self.assertIn("exit code 1", str(self.ws_api._error))
        self.assertIn("Process failed exit code 1", str(self.ws_api._error))
        self.assertEqual(result, 1)

    def test_on_message_with_aws_command_exit_code_uses_aws_error_handler(self):
        """Test that _on_message uses AWS-specific error handling for AWS commands"""
        message = self._create_mock_message("AWS operation failed exit code 1")
        self.ws_api._request = {"command": ["aws"]}  # type: ignore

        with patch("cpln.utils.websocket.AwsExitCode") as mock_aws_exit_code:
            mock_aws_exit_code.is_error.return_value = True
            mock_aws_exit_code.get_error_type.return_value = "AWS_ERROR"
            mock_aws_exit_code.get_message.return_value = "AWS command failed"

            result = self.ws_api._on_message(self.mock_ws, message)  # type: ignore

            mock_aws_exit_code.is_error.assert_called_once_with(1)
            mock_aws_exit_code.get_error_type.assert_called_once_with(1)
            mock_aws_exit_code.get_message.assert_called_once_with(1)
            self.assertIsInstance(self.ws_api._error, WebSocketExitCodeError)
            self.assertEqual(result, 1)

    def test_on_message_with_postgres_commands_uses_postgres_error_handler(self):
        """Test that _on_message uses Postgres-specific error handling for pg commands"""
        postgres_commands = ["pg_dump", "pg_restore"]

        for command in postgres_commands:
            with self.subTest(command=command):
                self.ws_api._error = None  # Reset error state
                message = self._create_mock_message(f"{command} failed exit code 2")
                self.ws_api._request = {"command": [command]}  # type: ignore

                with patch(
                    "cpln.utils.websocket.PostgresExitCode"
                ) as mock_pg_exit_code:
                    mock_pg_exit_code.is_error.return_value = True
                    mock_pg_exit_code.get_error_type.return_value = "POSTGRES_ERROR"
                    mock_pg_exit_code.get_message.return_value = (
                        f"{command} operation failed"
                    )

                    result = self.ws_api._on_message(self.mock_ws, message)  # type: ignore

                    mock_pg_exit_code.is_error.assert_called_once_with(2)
                    mock_pg_exit_code.get_error_type.assert_called_once_with(2)
                    mock_pg_exit_code.get_message.assert_called_once_with(2, command)
                    self.assertIsInstance(self.ws_api._error, WebSocketExitCodeError)
                    self.assertEqual(result, 2)

    def test_on_message_with_generic_command_uses_generic_error_handler(self):
        """Test that _on_message uses generic error handling for other commands"""
        message = self._create_mock_message("Generic command failed exit code 127")
        self.ws_api._request = {"command": ["unknown_command"]}  # type: ignore

        with patch("cpln.utils.websocket.GenericExitCode") as mock_generic_exit_code:
            mock_generic_exit_code.is_error.return_value = True
            mock_generic_exit_code.get_error_type.return_value = "GENERIC_ERROR"
            mock_generic_exit_code.get_message.return_value = "Command not found"

            result = self.ws_api._on_message(self.mock_ws, message)  # type: ignore

            mock_generic_exit_code.is_error.assert_called_once_with(127)
            mock_generic_exit_code.get_error_type.assert_called_once_with(127)
            mock_generic_exit_code.get_message.assert_called_once_with(127)
            self.assertIsInstance(self.ws_api._error, WebSocketExitCodeError)
            self.assertEqual(result, 127)

    def test_on_message_with_invalid_exit_code_format_handles_gracefully(self):
        """Test that _on_message handles invalid exit code formats gracefully"""
        message = self._create_mock_message("Process failed exit code abc")
        self.ws_api._request = {"command": ["test"]}  # type: ignore

        result = self.ws_api._on_message(self.mock_ws, message)  # type: ignore

        # Should not set error since exit code parsing failed and defaults to 0
        self.assertIsNone(self.ws_api._error)
        self.assertEqual(result, 0)


class TestCommandExecution(unittest.TestCase):
    """Test full command execution workflow"""

    def setUp(self):
        """Set up common test fixtures"""
        self.remote_wss = "wss://test.example.com"
        self.ws_api = WebSocketAPI(self.remote_wss)

    @patch("cpln.utils.websocket.WebSocketApp")
    def test_exec_with_successful_execution_returns_request_parameters(
        self, mock_websocket_app
    ):
        """Test that exec() returns request parameters for successful execution"""
        mock_ws_instance = MagicMock()
        mock_websocket_app.return_value = mock_ws_instance
        request_params = {
            "token": "abc123",
            "org": "myorg",
            "gvc": "mygvc",
            "container": "web",
            "command": "echo hello",
        }

        result = self.ws_api.exec(**request_params)

        self.assertEqual(result, request_params)
        self.assertEqual(self.ws_api._request, request_params)
        self.assertIsNone(self.ws_api._error)
        mock_ws_instance.run_forever.assert_called_once()

    @patch("cpln.utils.websocket.WebSocketApp")
    def test_exec_with_connection_error_raises_websocket_connection_error(
        self, mock_websocket_app
    ):
        """Test that exec() raises WebSocketConnectionError when connection error occurs"""
        mock_ws_instance = MagicMock()
        mock_websocket_app.return_value = mock_ws_instance

        # Simulate error occurring during run_forever execution
        def simulate_connection_error():
            self.ws_api._error = WebSocketConnectionError("Connection failed")

        mock_ws_instance.run_forever.side_effect = simulate_connection_error

        with self.assertRaises(WebSocketConnectionError) as context:
            self.ws_api.exec(command="test")

        self.assertIn("Connection failed", str(context.exception))
        mock_ws_instance.run_forever.assert_called_once()

    @patch("cpln.utils.websocket.WebSocketApp")
    def test_exec_with_exit_code_error_raises_websocket_exit_code_error(
        self, mock_websocket_app
    ):
        """Test that exec() raises WebSocketExitCodeError when command fails"""
        mock_ws_instance = MagicMock()
        mock_websocket_app.return_value = mock_ws_instance

        # Simulate error occurring during run_forever execution
        def simulate_exit_code_error():
            self.ws_api._error = WebSocketExitCodeError(
                "Command failed with exit code 1"
            )

        mock_ws_instance.run_forever.side_effect = simulate_exit_code_error

        with self.assertRaises(WebSocketExitCodeError) as context:
            self.ws_api.exec(command="test")

        self.assertIn("exit code 1", str(context.exception))
        mock_ws_instance.run_forever.assert_called_once()

    @patch("cpln.utils.websocket.WebSocketApp")
    def test_exec_resets_error_state_before_execution(self, mock_websocket_app):
        """Test that exec() resets error state before each execution"""
        mock_ws_instance = MagicMock()
        mock_websocket_app.return_value = mock_ws_instance
        self.ws_api._error = WebSocketConnectionError("Previous error")  # type: ignore

        result = self.ws_api.exec(command="test")

        # Should succeed since error state was reset and no new error occurred
        self.assertEqual(result, {"command": "test"})
        self.assertIsNone(self.ws_api._error)


class TestErrorHandlingAndEdgeCases(unittest.TestCase):
    """Test error handling and edge cases"""

    def setUp(self):
        """Set up common test fixtures"""
        self.remote_wss = "wss://test.example.com"
        self.ws_api = WebSocketAPI(self.remote_wss)
        self.mock_ws = MagicMock()

    def test_websocket_api_with_empty_url_initializes_correctly(self):
        """Test that WebSocketAPI handles empty URL gracefully"""
        ws_api = WebSocketAPI("")

        self.assertEqual(ws_api.remote_wss, "")
        self.assertIsNone(ws_api._request)
        self.assertIsNone(ws_api._error)

    def test_on_message_with_decode_exception_sets_operation_error(self):
        """Test that _on_message handles message decode exceptions"""
        # Create a mock message that will cause decode to fail
        mock_message = MagicMock()
        mock_message.decode.side_effect = UnicodeDecodeError(
            "utf-8", b"\xff\xfe", 0, 2, "invalid start byte"
        )

        self.ws_api._on_message(self.mock_ws, mock_message)

        self.assertIsInstance(self.ws_api._error, WebSocketOperationError)
        self.assertIn("Error processing message", str(self.ws_api._error))
        self.mock_ws.sock.close.assert_called_once()

    def test_on_close_with_various_abnormal_codes_sets_appropriate_errors(self):
        """Test that _on_close handles various abnormal closure codes"""
        abnormal_codes = [1001, 1002, 1003, 1006, 1011, 1015]

        for code in abnormal_codes:
            with self.subTest(close_code=code):
                self.ws_api._error = None  # Reset error state
                close_message = f"Abnormal closure {code}"

                self.ws_api._on_close(self.mock_ws, code, close_message)

                self.assertIsInstance(self.ws_api._error, WebSocketConnectionError)
                self.assertIn(str(code), str(self.ws_api._error))
                self.assertIn(close_message, str(self.ws_api._error))

    def test_on_error_with_none_error_message_handles_gracefully(self):
        """Test that _on_error handles None error message gracefully"""
        self.ws_api._on_error(self.mock_ws, None)  # type: ignore

        self.assertIsInstance(self.ws_api._error, WebSocketConnectionError)
        self.assertIn("WebSocket error", str(self.ws_api._error))
        self.assertIn("None", str(self.ws_api._error))

    @patch("cpln.utils.websocket.WebSocketApp")
    def test_exec_with_no_parameters_executes_successfully(self, mock_websocket_app):
        """Test that exec() works with no parameters"""
        mock_ws_instance = MagicMock()
        mock_websocket_app.return_value = mock_ws_instance

        result = self.ws_api.exec()

        self.assertEqual(result, {})
        self.assertEqual(self.ws_api._request, {})
        mock_ws_instance.run_forever.assert_called_once()


if __name__ == "__main__":
    unittest.main()  # type: ignore
