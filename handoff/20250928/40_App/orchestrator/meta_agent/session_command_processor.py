"""
Session Command Processor - Process user commands from Redis session data

This module implements the command consumption logic for SessionCommandInput,
allowing the AutonomousExecutor to respond to user commands in real-time.

Issue: #2242 - Wire session commands from Redis into AutonomousExecutor loop
Epic: #2311 - MorningAI Production Readiness & Feature Integration
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class QuickCommandType(Enum):
    """
    Valid quick command types that can be sent from SessionCommandInput.

    MAINTENANCE NOTE: When adding new quick commands, update these 3 locations:
      1. Backend API: VALID_QUICK_COMMAND_IDS in sessions.py
      2. Frontend: QUICK_COMMANDS in SessionCommandInput.jsx
      3. This enum and _handle_quick_command method
    """
    CONTINUE = "continue"
    EXPLAIN = "explain"
    SKIP = "skip"
    RETRY = "retry"


class CommandType(Enum):
    """Command types supported by the session command API"""
    USER_COMMAND = "user_command"
    QUICK_COMMAND = "quick_command"


@dataclass
class SessionCommand:
    """Represents a command from the session command queue"""
    command_id: str
    command: str
    command_type: CommandType
    sent_by: str
    user_id: str
    client_timestamp: Optional[str] = None
    server_timestamp: Optional[str] = None
    processed: bool = False
    processed_at: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionCommand":
        """Create SessionCommand from dictionary (Redis session data format)"""
        return cls(
            command_id=data.get("command_id", ""),
            command=data.get("command", ""),
            command_type=CommandType(data.get("type", "user_command")),
            sent_by=data.get("sent_by", ""),
            user_id=data.get("user_id", ""),
            client_timestamp=data.get("client_timestamp"),
            server_timestamp=data.get("server_timestamp"),
            processed=data.get("processed", False),
            processed_at=data.get("processed_at"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Redis storage"""
        return {
            "command_id": self.command_id,
            "command": self.command,
            "type": self.command_type.value,
            "sent_by": self.sent_by,
            "user_id": self.user_id,
            "client_timestamp": self.client_timestamp,
            "server_timestamp": self.server_timestamp,
            "processed": self.processed,
            "processed_at": self.processed_at,
        }


@dataclass
class CommandResult:
    """Result of processing a session command"""
    command_id: str
    success: bool
    action_taken: str
    message: Optional[str] = None
    error: Optional[str] = None


class SessionCommandProcessor:
    """
    Processes session commands from Redis and executes corresponding actions.

    This processor is designed to be called from the AutonomousExecutor's
    main execution loop to handle user commands in real-time.

    Supported Quick Commands:
    - continue: Resume execution / push executor out of paused/escalated state
    - explain: Trigger explanation of current step, write to observations
    - skip: Mark current task as skipped, move to next
    - retry: Re-execute the last failed action

    User Commands (user_command type):
    - Passed to ProjectEngineerAgent as additional context / goal update
    """

    def __init__(
        self,
        on_continue: Optional[Callable[[], None]] = None,
        on_explain: Optional[Callable[[], str]] = None,
        on_skip: Optional[Callable[[], None]] = None,
        on_retry: Optional[Callable[[], None]] = None,
        on_user_command: Optional[Callable[[str], None]] = None,
    ):
        """
        Initialize the SessionCommandProcessor.

        Args:
            on_continue: Callback for 'continue' quick command
            on_explain: Callback for 'explain' quick command (returns explanation)
            on_skip: Callback for 'skip' quick command
            on_retry: Callback for 'retry' quick command
            on_user_command: Callback for user_command type (receives command text)
        """
        self.on_continue = on_continue
        self.on_explain = on_explain
        self.on_skip = on_skip
        self.on_retry = on_retry
        self.on_user_command = on_user_command

        # Track processed commands to avoid duplicates
        self._processed_command_ids: set = set()

        logger.info("[SessionCommandProcessor] Initialized")

    def process_pending_commands(
        self,
        session_data: Dict[str, Any],
    ) -> List[CommandResult]:
        """
        Process all pending commands from session data.

        This method should be called from the AutonomousExecutor's main loop
        to check for and process any pending user commands.

        Args:
            session_data: Session data dictionary from Redis

        Returns:
            List of CommandResult for each processed command
        """
        commands_list = session_data.get("commands", [])
        if not commands_list:
            return []

        results: List[CommandResult] = []

        for cmd_data in commands_list:
            # Skip already processed commands
            if cmd_data.get("processed"):
                continue

            command_id = cmd_data.get("command_id", "")

            # Skip if we've already processed this command in this session
            if command_id in self._processed_command_ids:
                continue

            try:
                command = SessionCommand.from_dict(cmd_data)
                result = self._process_command(command)
                results.append(result)

                # Mark as processed
                cmd_data["processed"] = True
                cmd_data["processed_at"] = datetime.utcnow().isoformat()
                self._processed_command_ids.add(command_id)

                logger.info(
                    "[SessionCommandProcessor] Processed command %s: %s -> %s",
                    command_id[:8],
                    command.command,
                    "success" if result.success else "failed"
                )

            except Exception as e:
                logger.error(
                    "[SessionCommandProcessor] Failed to process command %s: %s",
                    command_id[:8], e, exc_info=True
                )
                results.append(CommandResult(
                    command_id=command_id,
                    success=False,
                    action_taken="error",
                    error=str(e),
                ))

        return results

    def _process_command(self, command: SessionCommand) -> CommandResult:
        """
        Process a single session command.

        Args:
            command: The SessionCommand to process

        Returns:
            CommandResult with processing outcome
        """
        if command.command_type == CommandType.QUICK_COMMAND:
            return self._handle_quick_command(command)
        else:
            return self._handle_user_command(command)

    def _handle_quick_command(self, command: SessionCommand) -> CommandResult:
        """
        Handle a quick command (continue, explain, skip, retry).

        Args:
            command: The quick command to handle

        Returns:
            CommandResult with processing outcome
        """
        quick_cmd = command.command.lower()

        try:
            if quick_cmd == QuickCommandType.CONTINUE.value:
                if self.on_continue:
                    self.on_continue()
                return CommandResult(
                    command_id=command.command_id,
                    success=True,
                    action_taken="continue",
                    message="Execution resumed",
                )

            elif quick_cmd == QuickCommandType.EXPLAIN.value:
                explanation = None
                if self.on_explain:
                    explanation = self.on_explain()
                return CommandResult(
                    command_id=command.command_id,
                    success=True,
                    action_taken="explain",
                    message=explanation or "Explanation generated",
                )

            elif quick_cmd == QuickCommandType.SKIP.value:
                if self.on_skip:
                    self.on_skip()
                return CommandResult(
                    command_id=command.command_id,
                    success=True,
                    action_taken="skip",
                    message="Current task skipped",
                )

            elif quick_cmd == QuickCommandType.RETRY.value:
                if self.on_retry:
                    self.on_retry()
                return CommandResult(
                    command_id=command.command_id,
                    success=True,
                    action_taken="retry",
                    message="Retrying last action",
                )

            else:
                return CommandResult(
                    command_id=command.command_id,
                    success=False,
                    action_taken="unknown_quick_command",
                    error=f"Unknown quick command: {quick_cmd}",
                )

        except Exception as e:
            logger.error(
                "[SessionCommandProcessor] Quick command %s failed: %s",
                quick_cmd, e, exc_info=True
            )
            return CommandResult(
                command_id=command.command_id,
                success=False,
                action_taken=quick_cmd,
                error=str(e),
            )

    def _handle_user_command(self, command: SessionCommand) -> CommandResult:
        """
        Handle a user command (free-form text instruction).

        Args:
            command: The user command to handle

        Returns:
            CommandResult with processing outcome
        """
        try:
            if self.on_user_command:
                self.on_user_command(command.command)

            return CommandResult(
                command_id=command.command_id,
                success=True,
                action_taken="user_command",
                message=f"User command received: {command.command[:50]}...",
            )

        except Exception as e:
            logger.error(
                "[SessionCommandProcessor] User command failed: %s",
                e, exc_info=True
            )
            return CommandResult(
                command_id=command.command_id,
                success=False,
                action_taken="user_command",
                error=str(e),
            )

    def get_processed_count(self) -> int:
        """Return the number of commands processed in this session"""
        return len(self._processed_command_ids)

    def reset(self) -> None:
        """Reset the processor state (clear processed command tracking)"""
        self._processed_command_ids.clear()
        logger.info("[SessionCommandProcessor] State reset")
