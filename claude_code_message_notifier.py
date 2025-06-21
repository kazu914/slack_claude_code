#!/usr/bin/env python3
"""
Claude Code message notification control class

Controls frequent tool output notifications and sends Slack notifications
at appropriate timing
"""

from typing import List, Optional

from claude_code_sdk.types import (
    AssistantMessage,
    Message,
    ToolResultBlock,
    ToolUseBlock,
)

from message_utils import extract_message_text


class ClaudeCodeMessageNotifier:
    """
    A class that controls messages from Claude Code and adjusts tool output
    notification frequency

    Tool outputs are not notified immediately, but notifications are sent
    under these conditions:
    - When non-tool output occurs
    - When tool outputs continue consecutively for 10 times
    """

    def __init__(self) -> None:
        """Initialize"""
        self.tools_count = 0

    def process_message(self, message: Message) -> List[str]:
        """
        Process a message and return a list of messages to send to Slack

        Args:
            message: Claude Code SDK Message object

        Returns:
            List[str]: List of messages to send to Slack
        """
        message_text = extract_message_text(message)

        if self._is_tools_message(message, message_text):
            return self._handle_tools_message()
        else:
            return self._handle_non_tools_message(message_text)

    def _handle_tools_message(self) -> List[str]:
        """Process tools message"""
        self.tools_count += 1

        if self.tools_count % 10 == 0:
            # When it becomes a multiple of 10, notify and reset
            count = self.tools_count
            self.tools_count = 0
            return [f"Used tools {count} times"]

        # Don't notify yet
        return []

    def _handle_non_tools_message(self, message_text: Optional[str]) -> List[str]:
        """Process non-tools message"""
        messages_to_send = []

        # If there are accumulated tool notifications, send them first
        if self.tools_count > 0:
            messages_to_send.append(f"Used tools {self.tools_count} times")
            self.tools_count = 0

        # If current message contains text, add it
        if message_text:
            messages_to_send.append(message_text)

        return messages_to_send

    def _is_tools_message(self, message: Message, message_text: Optional[str]) -> bool:
        """
        Determine if a message is tool output

        Args:
            message: Claude Code SDK Message object
            message_text: Extracted message text

        Returns:
            bool: True if it's tool output
        """
        # Always tools if AssistantMessage contains Tool blocks
        if isinstance(message, AssistantMessage):
            has_tool_blocks = any(
                isinstance(block, (ToolUseBlock, ToolResultBlock))
                for block in message.content
            )
            if has_tool_blocks:
                return True

        # If UserMessage has content as list (tool_result, etc.)
        if hasattr(message, "content") and isinstance(message.content, list):
            return True

        # If message text is JSON data
        if message_text and (
            message_text.strip().startswith("[")
            or message_text.strip().startswith("{")
            or '"type":' in message_text
            or '"tool_use_id":' in message_text
        ):
            return True

        # If there's no text, it's likely tools or metadata
        if message_text is None:
            return True

        # Normal text message
        return False

    def get_pending_tools_notification(self) -> Optional[str]:
        """
        Get pending tool notification if available
        (used when processing is complete, etc.)

        Returns:
            Optional[str]: Pending tool notification message. None if none exists
        """
        if self.tools_count > 0:
            count = self.tools_count
            self.tools_count = 0
            return f"Used tools {count} times"
        return None

    def reset_count(self) -> None:
        """Reset tools count"""
        self.tools_count = 0

    @property
    def current_tools_count(self) -> int:
        """Get current tools count"""
        return self.tools_count
