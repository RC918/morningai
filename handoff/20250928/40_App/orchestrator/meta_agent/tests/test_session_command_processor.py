"""
Tests for SessionCommandProcessor - Issue #2242

Tests the session command processing logic that wires commands from Redis
into the AutonomousExecutor loop.
"""

import pytest
from unittest.mock import MagicMock

from meta_agent.session_command_processor import (
    SessionCommandProcessor,
    SessionCommand,
    CommandType,
    QuickCommandType,
)


class TestSessionCommand:
    """Tests for SessionCommand dataclass"""

    def test_from_dict_user_command(self):
        """Test creating SessionCommand from user_command dict"""
        data = {
            "command_id": "cmd-123",
            "command": "Please add error handling",
            "type": "user_command",
            "sent_by": "user@example.com",
            "user_id": "user-456",
            "client_timestamp": "2025-01-01T00:00:00",
            "server_timestamp": "2025-01-01T00:00:01",
            "processed": False,
        }
        cmd = SessionCommand.from_dict(data)

        assert cmd.command_id == "cmd-123"
        assert cmd.command == "Please add error handling"
        assert cmd.command_type == CommandType.USER_COMMAND
        assert cmd.sent_by == "user@example.com"
        assert cmd.user_id == "user-456"
        assert cmd.processed is False

    def test_from_dict_quick_command(self):
        """Test creating SessionCommand from quick_command dict"""
        data = {
            "command_id": "cmd-789",
            "command": "continue",
            "type": "quick_command",
            "sent_by": "user@example.com",
            "user_id": "user-456",
        }
        cmd = SessionCommand.from_dict(data)

        assert cmd.command_id == "cmd-789"
        assert cmd.command == "continue"
        assert cmd.command_type == CommandType.QUICK_COMMAND

    def test_to_dict(self):
        """Test converting SessionCommand to dict"""
        cmd = SessionCommand(
            command_id="cmd-123",
            command="skip",
            command_type=CommandType.QUICK_COMMAND,
            sent_by="user@example.com",
            user_id="user-456",
            processed=True,
            processed_at="2025-01-01T00:00:02",
        )
        data = cmd.to_dict()

        assert data["command_id"] == "cmd-123"
        assert data["command"] == "skip"
        assert data["type"] == "quick_command"
        assert data["processed"] is True
        assert data["processed_at"] == "2025-01-01T00:00:02"


class TestQuickCommandType:
    """Tests for QuickCommandType enum"""

    def test_valid_quick_commands(self):
        """Test all valid quick command types"""
        assert QuickCommandType.CONTINUE.value == "continue"
        assert QuickCommandType.EXPLAIN.value == "explain"
        assert QuickCommandType.SKIP.value == "skip"
        assert QuickCommandType.RETRY.value == "retry"


class TestSessionCommandProcessor:
    """Tests for SessionCommandProcessor"""

    def test_init(self):
        """Test processor initialization"""
        processor = SessionCommandProcessor()
        assert processor.get_processed_count() == 0

    def test_process_empty_commands(self):
        """Test processing session data with no commands"""
        processor = SessionCommandProcessor()
        session_data = {"commands": []}

        results = processor.process_pending_commands(session_data)

        assert results == []
        assert processor.get_processed_count() == 0

    def test_process_no_commands_key(self):
        """Test processing session data without commands key"""
        processor = SessionCommandProcessor()
        session_data = {}

        results = processor.process_pending_commands(session_data)

        assert results == []

    def test_skip_already_processed_commands(self):
        """Test that already processed commands are skipped"""
        processor = SessionCommandProcessor()
        session_data = {
            "commands": [
                {
                    "command_id": "cmd-123",
                    "command": "continue",
                    "type": "quick_command",
                    "sent_by": "user@example.com",
                    "user_id": "user-456",
                    "processed": True,
                    "processed_at": "2025-01-01T00:00:00",
                }
            ]
        }

        results = processor.process_pending_commands(session_data)

        assert results == []

    def test_process_continue_command(self):
        """Test processing 'continue' quick command"""
        on_continue = MagicMock()
        processor = SessionCommandProcessor(on_continue=on_continue)
        session_data = {
            "commands": [
                {
                    "command_id": "cmd-123",
                    "command": "continue",
                    "type": "quick_command",
                    "sent_by": "user@example.com",
                    "user_id": "user-456",
                }
            ]
        }

        results = processor.process_pending_commands(session_data)

        assert len(results) == 1
        assert results[0].success is True
        assert results[0].action_taken == "continue"
        on_continue.assert_called_once()
        assert session_data["commands"][0]["processed"] is True
        assert "processed_at" in session_data["commands"][0]

    def test_process_explain_command(self):
        """Test processing 'explain' quick command"""
        on_explain = MagicMock(return_value="Current status: running")
        processor = SessionCommandProcessor(on_explain=on_explain)
        session_data = {
            "commands": [
                {
                    "command_id": "cmd-123",
                    "command": "explain",
                    "type": "quick_command",
                    "sent_by": "user@example.com",
                    "user_id": "user-456",
                }
            ]
        }

        results = processor.process_pending_commands(session_data)

        assert len(results) == 1
        assert results[0].success is True
        assert results[0].action_taken == "explain"
        assert results[0].message == "Current status: running"
        on_explain.assert_called_once()

    def test_process_skip_command(self):
        """Test processing 'skip' quick command"""
        on_skip = MagicMock()
        processor = SessionCommandProcessor(on_skip=on_skip)
        session_data = {
            "commands": [
                {
                    "command_id": "cmd-123",
                    "command": "skip",
                    "type": "quick_command",
                    "sent_by": "user@example.com",
                    "user_id": "user-456",
                }
            ]
        }

        results = processor.process_pending_commands(session_data)

        assert len(results) == 1
        assert results[0].success is True
        assert results[0].action_taken == "skip"
        on_skip.assert_called_once()

    def test_process_retry_command(self):
        """Test processing 'retry' quick command"""
        on_retry = MagicMock()
        processor = SessionCommandProcessor(on_retry=on_retry)
        session_data = {
            "commands": [
                {
                    "command_id": "cmd-123",
                    "command": "retry",
                    "type": "quick_command",
                    "sent_by": "user@example.com",
                    "user_id": "user-456",
                }
            ]
        }

        results = processor.process_pending_commands(session_data)

        assert len(results) == 1
        assert results[0].success is True
        assert results[0].action_taken == "retry"
        on_retry.assert_called_once()

    def test_process_user_command(self):
        """Test processing user_command type"""
        on_user_command = MagicMock()
        processor = SessionCommandProcessor(on_user_command=on_user_command)
        session_data = {
            "commands": [
                {
                    "command_id": "cmd-123",
                    "command": "Please add more tests",
                    "type": "user_command",
                    "sent_by": "user@example.com",
                    "user_id": "user-456",
                }
            ]
        }

        results = processor.process_pending_commands(session_data)

        assert len(results) == 1
        assert results[0].success is True
        assert results[0].action_taken == "user_command"
        on_user_command.assert_called_once_with("Please add more tests")

    def test_process_multiple_commands(self):
        """Test processing multiple commands in sequence"""
        on_continue = MagicMock()
        on_skip = MagicMock()
        processor = SessionCommandProcessor(
            on_continue=on_continue,
            on_skip=on_skip,
        )
        session_data = {
            "commands": [
                {
                    "command_id": "cmd-1",
                    "command": "continue",
                    "type": "quick_command",
                    "sent_by": "user@example.com",
                    "user_id": "user-456",
                },
                {
                    "command_id": "cmd-2",
                    "command": "skip",
                    "type": "quick_command",
                    "sent_by": "user@example.com",
                    "user_id": "user-456",
                },
            ]
        }

        results = processor.process_pending_commands(session_data)

        assert len(results) == 2
        assert results[0].action_taken == "continue"
        assert results[1].action_taken == "skip"
        assert processor.get_processed_count() == 2

    def test_unknown_quick_command(self):
        """Test handling unknown quick command"""
        processor = SessionCommandProcessor()
        session_data = {
            "commands": [
                {
                    "command_id": "cmd-123",
                    "command": "unknown_command",
                    "type": "quick_command",
                    "sent_by": "user@example.com",
                    "user_id": "user-456",
                }
            ]
        }

        results = processor.process_pending_commands(session_data)

        assert len(results) == 1
        assert results[0].success is False
        assert results[0].action_taken == "unknown_quick_command"
        assert "Unknown quick command" in results[0].error

    def test_callback_exception_handling(self):
        """Test that callback exceptions are handled gracefully"""
        on_continue = MagicMock(side_effect=Exception("Callback error"))
        processor = SessionCommandProcessor(on_continue=on_continue)
        session_data = {
            "commands": [
                {
                    "command_id": "cmd-123",
                    "command": "continue",
                    "type": "quick_command",
                    "sent_by": "user@example.com",
                    "user_id": "user-456",
                }
            ]
        }

        results = processor.process_pending_commands(session_data)

        assert len(results) == 1
        assert results[0].success is False
        assert "Callback error" in results[0].error

    def test_reset(self):
        """Test resetting processor state"""
        processor = SessionCommandProcessor()
        session_data = {
            "commands": [
                {
                    "command_id": "cmd-123",
                    "command": "continue",
                    "type": "quick_command",
                    "sent_by": "user@example.com",
                    "user_id": "user-456",
                }
            ]
        }

        processor.process_pending_commands(session_data)
        assert processor.get_processed_count() == 1

        processor.reset()
        assert processor.get_processed_count() == 0

    def test_idempotent_processing(self):
        """Test that same command is not processed twice"""
        on_continue = MagicMock()
        processor = SessionCommandProcessor(on_continue=on_continue)
        session_data = {
            "commands": [
                {
                    "command_id": "cmd-123",
                    "command": "continue",
                    "type": "quick_command",
                    "sent_by": "user@example.com",
                    "user_id": "user-456",
                }
            ]
        }

        # First call
        results1 = processor.process_pending_commands(session_data)
        assert len(results1) == 1

        # Second call - should not process again
        results2 = processor.process_pending_commands(session_data)
        assert len(results2) == 0

        # Callback should only be called once
        on_continue.assert_called_once()


class TestQuickCommandValidation:
    """
    Tests for quick command validation.

    MAINTENANCE NOTE: When adding new quick commands, update these 3 locations:
      1. Backend API: VALID_QUICK_COMMAND_IDS in sessions.py
      2. Frontend: QUICK_COMMANDS in SessionCommandInput.jsx
      3. QuickCommandType enum in session_command_processor.py
    """

    @pytest.mark.parametrize("quick_cmd", ["continue", "explain", "skip", "retry"])
    def test_valid_quick_commands_are_processed(self, quick_cmd):
        """Test that all valid quick commands are processed successfully"""
        processor = SessionCommandProcessor()
        session_data = {
            "commands": [
                {
                    "command_id": f"cmd-{quick_cmd}",
                    "command": quick_cmd,
                    "type": "quick_command",
                    "sent_by": "user@example.com",
                    "user_id": "user-456",
                }
            ]
        }

        results = processor.process_pending_commands(session_data)

        assert len(results) == 1
        assert results[0].success is True
        assert results[0].action_taken == quick_cmd
