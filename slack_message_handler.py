#!/usr/bin/env python3
"""
Slack Message Handler for Claude Code Integration

Handles Slack-specific message processing and sending operations
"""

import logging
import traceback
from datetime import datetime
from typing import Any, Dict, Optional


class SlackMessageHandler:
    """
    Handles Slack message operations for the Claude Code integration

    Responsibilities:
    - Send messages to Slack threads
    - Format error messages for Slack
    - Add auto-send prefixes
    - Handle completion notifications
    """

    def __init__(self, logger: logging.Logger) -> None:
        """
        Initialize Slack message handler

        Args:
            logger: Logger instance
        """
        self.logger = logger

    def add_auto_send_prefix(self, message: str) -> str:
        """Add auto-send prefix to distinguish Python-generated messages."""
        return f"[Auto-sent] {message}"

    async def send_thread_reply(
        self, client: Any, channel_id: str, thread_ts: str, text: str
    ) -> Any:
        """
        Send a reply to a Slack thread with auto-send prefix

        Args:
            client: Slack client
            channel_id: Slack channel ID
            thread_ts: Thread timestamp
            text: Message text

        Returns:
            Slack response
        """
        try:
            # Add auto-send prefix to all messages sent through this function
            prefixed_text = self.add_auto_send_prefix(text)

            # Use the synchronous client method in async context
            response = client.chat_postMessage(
                channel=channel_id, thread_ts=thread_ts, text=prefixed_text, mrkdwn=True
            )
            self.logger.debug(f"Sent thread reply: {text[:50]}...")
            return response
        except Exception as e:
            self.logger.error(f"Error sending thread reply: {e}")
            return None

    async def send_initial_acknowledgment(
        self, client: Any, channel_id: str, thread_ts: str
    ) -> None:
        """
        Send initial acknowledgment message

        Args:
            client: Slack client
            channel_id: Slack channel ID
            thread_ts: Thread timestamp
        """
        await self.send_thread_reply(
            client,
            channel_id,
            thread_ts,
            "Instructions confirmed. Starting processing...",
        )

    async def send_completion_notification(
        self, client: Any, channel_id: str, thread_ts: str, message_count: int
    ) -> None:
        """
        Send notification when Claude Code processing is completed

        Args:
            client: Slack client
            channel_id: Slack channel ID
            thread_ts: Thread timestamp
            message_count: Number of messages processed
        """
        try:
            completion_message = "✅ Claude Code processing completed"

            await self.send_thread_reply(
                client,
                channel_id,
                thread_ts,
                completion_message,
            )

            self.logger.info(
                f"Claude Code completion notification sent for {message_count} messages"
            )

        except Exception as e:
            self.logger.error(
                f"Failed to send Claude Code completion notification: {e}"
            )

    async def send_detailed_error_to_slack(
        self,
        client: Any,
        channel_id: str,
        thread_ts: str,
        error_details: Dict[str, str],
    ) -> Any:
        """
        Send detailed error information to Slack

        Args:
            client: Slack client
            channel_id: Slack channel ID
            thread_ts: Thread timestamp
            error_details: Dictionary containing error information

        Returns:
            Slack response
        """
        try:
            # Create a user-friendly error message
            error_message = f"""🚨 **An error occurred**

**Error Type**: {error_details["error_type"]}
**Error Message**: {error_details["error_message"]}
**Location**: {error_details["function"]}

**Details**:
```
{error_details.get("context", "No context information available")}
```

Detailed stack trace has been logged to the log file.
Log file: `logs/slack_monitor_{datetime.now().strftime("%Y%m%d")}.log`"""

            # Send to Slack through send_thread_reply (auto-prefix will be added)
            response = await self.send_thread_reply(
                client,
                channel_id,
                thread_ts,
                error_message,
            )

            self.logger.info(
                f"Detailed error sent to Slack: {error_details['error_type']}"
            )
            return response

        except Exception as e:
            self.logger.error(f"Failed to send detailed error to Slack: {e}")
            # Fallback to simple error message
            try:
                error_type = error_details["error_type"]
                error_message = error_details["error_message"]
                simple_error = f"An error occurred: {error_type} - {error_message}"
                await self.send_thread_reply(
                    client,
                    channel_id,
                    thread_ts,
                    simple_error,
                )
            except Exception as fallback_error:
                self.logger.critical(
                    f"Failed to send even simple error message: {fallback_error}"
                )
            return None

    def create_error_details(
        self, error: Exception, function_name: str, context: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Create error details dictionary

        Args:
            error: Exception object
            function_name: Name of the function where error occurred
            context: Additional context information

        Returns:
            Dictionary containing error details
        """
        error_details = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
            "function": function_name,
        }

        if context:
            error_details["context"] = context

        return error_details

    async def send_claude_code_error_message(
        self,
        client: Any,
        channel_id: str,
        thread_ts: str,
        error_type: str,
        custom_message: str,
    ) -> None:
        """
        Send Claude Code specific error messages

        Args:
            client: Slack client
            channel_id: Slack channel ID
            thread_ts: Thread timestamp
            error_type: Type of Claude Code error
            custom_message: Custom error message
        """
        await self.send_thread_reply(client, channel_id, thread_ts, custom_message)

        self.logger.error(f"Claude Code {error_type}: {custom_message}")

    def log_message_details(
        self, user_id: str, channel_id: str, thread_ts: str, text: str
    ) -> None:
        """
        Log message details

        Args:
            user_id: Slack user ID
            channel_id: Slack channel ID
            thread_ts: Thread timestamp
            text: Message text
        """
        self.logger.info(
            f"Message detected from user {user_id} in channel {channel_id}"
        )
        self.logger.info(f"Thread TS: {thread_ts}")
        self.logger.debug(f"Message: {text}")
