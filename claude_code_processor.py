#!/usr/bin/env python3
"""
Claude Code Processor for Slack Integration

Handles Claude Code SDK integration and processing operations
"""

import logging
from pathlib import Path
from typing import Any, Dict, List

from claude_code_sdk import (
    ClaudeCodeOptions,
    CLIConnectionError,
    CLIJSONDecodeError,
    CLINotFoundError,
    Message,
    ProcessError,
    query,
)

from claude_code_message_notifier import ClaudeCodeMessageNotifier
from configuration_manager import ConfigurationManager
from slack_message_handler import SlackMessageHandler


class ClaudeCodeProcessor:
    """
    Handles Claude Code SDK integration and processing

    Responsibilities:
    - Process user requests with Claude Code SDK
    - Create and manage Claude Code options
    - Handle Claude Code specific errors
    - Manage message flow with notification control
    """

    def __init__(
        self,
        config_manager: ConfigurationManager,
        message_handler: SlackMessageHandler,
        logger: logging.Logger,
    ) -> None:
        """
        Initialize Claude Code processor

        Args:
            config_manager: Configuration manager instance
            message_handler: Slack message handler instance
            logger: Logger instance
        """
        self.config_manager = config_manager
        self.message_handler = message_handler
        self.logger = logger

    def _add_optional_options(
        self, options_dict: Dict[str, Any], config: Dict[str, Any]
    ) -> None:
        """Add optional configuration parameters to options dictionary"""
        optional_params = [
            "allowed_tools",
            "max_thinking_tokens",
            "append_system_prompt",
            "mcp_tools",
            "mcp_servers",
            "continue_conversation",
            "resume",
            "max_turns",
            "disallowed_tools",
            "model",
            "permission_prompt_tool_name",
        ]

        for param in optional_params:
            if config.get(param) is not None:
                if param == "append_system_prompt" and not config.get(param):
                    continue  # Skip empty strings
                options_dict[param] = config[param]

    def _create_claude_code_options(
        self, channel_id: str, system_prompt: str
    ) -> ClaudeCodeOptions:
        """
        Create ClaudeCodeOptions based on channel configuration

        Args:
            channel_id: Slack channel ID
            system_prompt: System prompt for Claude Code

        Returns:
            ClaudeCodeOptions instance
        """
        config = self.config_manager.get_channel_config(channel_id)

        # Validate configuration
        self.config_manager.validate_channel_config(channel_id)

        # Build options dictionary with required values
        options_dict = {
            "system_prompt": system_prompt,
            "cwd": Path(config["cwd"]),
            "permission_mode": config["permission_mode"],
        }

        # Add optional parameters
        self._add_optional_options(options_dict, config)

        return ClaudeCodeOptions(**options_dict)

    async def process_with_claude_code(
        self, client: Any, channel_id: str, thread_ts: str, user_text: str, user_id: str
    ) -> None:
        """
        Process user request with Claude Code SDK

        Args:
            client: Slack client
            channel_id: Slack channel ID
            thread_ts: Thread timestamp
            user_text: User message text
            user_id: Slack user ID
        """
        try:
            # Create system prompt and options
            system_prompt = self.config_manager.create_system_prompt(
                thread_ts, user_id, channel_id
            )
            options = self._create_claude_code_options(channel_id, system_prompt)

            # Execute the Claude Code query
            messages = await self._execute_claude_code_query(
                client, channel_id, thread_ts, user_text, options
            )

            # Send completion notification
            await self.message_handler.send_completion_notification(
                client, channel_id, thread_ts, len(messages)
            )

        except ValueError as e:
            await self._handle_configuration_error(
                client, channel_id, thread_ts, e, user_id
            )
        except Exception as e:
            await self._handle_general_error(client, channel_id, thread_ts, e, user_id)

    async def _execute_claude_code_query(
        self,
        client: Any,
        channel_id: str,
        thread_ts: str,
        user_text: str,
        options: ClaudeCodeOptions,
    ) -> List[Message]:
        """
        Execute Claude Code query with error handling

        Args:
            client: Slack client
            channel_id: Slack channel ID
            thread_ts: Thread timestamp
            user_text: User message text
            options: Claude Code options

        Returns:
            List of processed messages
        """
        self.logger.info(f"Starting Claude Code query for channel {channel_id}...")

        messages: List[Message] = []
        notifier = ClaudeCodeMessageNotifier()

        try:
            prompt = (
                f"Follow the user instructions received in Slack.\n\n"
                f"User instructions:\n{user_text}"
            )

            async for message in query(prompt=prompt, options=options):
                await self._process_claude_message(
                    client, channel_id, thread_ts, message, notifier
                )
                messages.append(message)

        except CLIJSONDecodeError as e:
            await self._handle_json_decode_error(
                client, channel_id, thread_ts, e, len(messages)
            )
        except CLIConnectionError as e:
            await self._handle_connection_error(client, channel_id, thread_ts, e)
            return messages
        except CLINotFoundError as e:
            await self._handle_cli_not_found_error(client, channel_id, thread_ts, e)
            return messages
        except ProcessError as e:
            await self._handle_process_error(
                client, channel_id, thread_ts, e, len(messages)
            )

        # Send any pending tools notification
        await self._send_pending_notification(client, channel_id, thread_ts, notifier)

        return messages

    async def _process_claude_message(
        self,
        client: Any,
        channel_id: str,
        thread_ts: str,
        message: Message,
        notifier: ClaudeCodeMessageNotifier,
    ) -> None:
        """
        Process a single Claude Code message

        Args:
            client: Slack client
            channel_id: Slack channel ID
            thread_ts: Thread timestamp
            message: Claude Code message
            notifier: Message notifier instance
        """
        # Process message with notifier
        messages_to_send = notifier.process_message(message)

        # Send messages returned by notifier
        for msg in messages_to_send:
            self.logger.info(f"Claude Code: {msg}")
            await self.message_handler.send_thread_reply(
                client, channel_id, thread_ts, msg
            )

        # Log metadata messages that were not sent
        if not messages_to_send:
            self.logger.debug(f"Claude Code [tools/metadata]: {type(message).__name__}")

    async def _send_pending_notification(
        self,
        client: Any,
        channel_id: str,
        thread_ts: str,
        notifier: ClaudeCodeMessageNotifier,
    ) -> None:
        """
        Send pending tools notification if available

        Args:
            client: Slack client
            channel_id: Slack channel ID
            thread_ts: Thread timestamp
            notifier: Message notifier instance
        """
        pending_notification = notifier.get_pending_tools_notification()
        if pending_notification:
            self.logger.info(f"Claude Code: {pending_notification}")
            await self.message_handler.send_thread_reply(
                client, channel_id, thread_ts, pending_notification
            )

    async def _handle_configuration_error(
        self,
        client: Any,
        channel_id: str,
        thread_ts: str,
        error: ValueError,
        user_id: str,
    ) -> None:
        """
        Handle configuration errors

        Args:
            client: Slack client
            channel_id: Slack channel ID
            thread_ts: Thread timestamp
            error: ValueError instance
            user_id: Slack user ID
        """
        error_details = self.message_handler.create_error_details(
            error,
            "_process_with_claude_code",
            f"Channel: {channel_id}, User: {user_id}",
        )

        self.logger.error(f"Configuration error: {error_details['error_message']}")
        self.logger.error(f"Full traceback:\n{error_details['traceback']}")
        await self.message_handler.send_detailed_error_to_slack(
            client, channel_id, thread_ts, error_details
        )

    async def _handle_general_error(
        self,
        client: Any,
        channel_id: str,
        thread_ts: str,
        error: Exception,
        user_id: str,
    ) -> None:
        """
        Handle general exceptions

        Args:
            client: Slack client
            channel_id: Slack channel ID
            thread_ts: Thread timestamp
            error: Exception instance
            user_id: Slack user ID
        """
        error_details = self.message_handler.create_error_details(
            error,
            "_process_with_claude_code",
            f"Channel: {channel_id}, User: {user_id}",
        )

        error_type = error_details["error_type"]
        error_message = error_details["error_message"]
        self.logger.error(
            f"Error processing with Claude Code: {error_type}: {error_message}"
        )
        self.logger.error(f"Full traceback:\n{error_details['traceback']}")
        await self.message_handler.send_detailed_error_to_slack(
            client, channel_id, thread_ts, error_details
        )

    async def _handle_json_decode_error(
        self,
        client: Any,
        channel_id: str,
        thread_ts: str,
        error: CLIJSONDecodeError,
        message_count: int,
    ) -> None:
        """Handle JSON decode errors gracefully"""
        self.logger.error(f"Claude Code JSON parsing error: {str(error)}")
        self.logger.info(f"Processed {message_count} messages before error occurred")

        # Notify user about the issue but continue processing
        await self.message_handler.send_claude_code_error_message(
            client,
            channel_id,
            thread_ts,
            "JSON parsing error",
            "⚠️ A data parsing error occurred during processing, "
            "but partial results will be provided.",
        )

    async def _handle_connection_error(
        self, client: Any, channel_id: str, thread_ts: str, error: CLIConnectionError
    ) -> None:
        """Handle connection errors"""
        await self.message_handler.send_claude_code_error_message(
            client,
            channel_id,
            thread_ts,
            "connection error",
            "❌ An error occurred connecting to Claude Code. "
            "Please wait and try again.",
        )

    async def _handle_cli_not_found_error(
        self, client: Any, channel_id: str, thread_ts: str, error: CLINotFoundError
    ) -> None:
        """Handle CLI not found errors"""
        await self.message_handler.send_claude_code_error_message(
            client,
            channel_id,
            thread_ts,
            "CLI not found",
            "❌ Claude Code CLI not found. Please check the installation.",
        )

    async def _handle_process_error(
        self,
        client: Any,
        channel_id: str,
        thread_ts: str,
        error: ProcessError,
        message_count: int,
    ) -> None:
        """Handle process errors"""
        self.logger.error(
            f"Claude Code process error: {str(error)}, exit code: {error.exit_code}"
        )
        self.logger.info(f"Processed {message_count} messages before process error")

        await self.message_handler.send_claude_code_error_message(
            client,
            channel_id,
            thread_ts,
            "process error",
            f"⚠️ An error occurred in the Claude Code process "
            f"(exit code: {error.exit_code}). "
            "Partial results will be provided.",
        )
