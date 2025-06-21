#!/usr/bin/env python3

import asyncio
import sys
import traceback
from datetime import datetime
from typing import Any

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from claude_code_processor import ClaudeCodeProcessor
from configuration_manager import ConfigurationManager
from logging_manager import LoggingManager
from slack_message_handler import SlackMessageHandler


class SlackSocketMonitor:
    def __init__(self) -> None:
        # Initialize configuration manager
        self.config_manager = ConfigurationManager()

        # Initialize logging manager
        self.logging_manager = LoggingManager()
        self.logger = self.logging_manager.get_logger()

        # Initialize message handler
        self.message_handler = SlackMessageHandler(self.logger)

        # Initialize Claude Code processor
        self.claude_processor = ClaudeCodeProcessor(
            self.config_manager, self.message_handler, self.logger
        )

        # Initialize Slack app
        slack_bot_token = self.config_manager.get_slack_bot_token()
        self.app = App(token=slack_bot_token)

        # Get Claude user ID for filtering
        self.claude_user_id = self.config_manager.get_claude_user_id()

        self.setup_event_handlers()

        # Log initialization info
        channels_count = self.config_manager.get_channels_count()
        self.logging_manager.log_initialization_info(
            self.claude_user_id, channels_count
        )

    def setup_event_handlers(self) -> None:
        """Setup Slack event handlers"""

        @self.app.event("message")
        def handle_message(event: Any, say: Any, client: Any) -> None:
            """Handle messages in monitored channels"""

            # Skip bot messages
            if event.get("bot_id") or event.get("user") == self.claude_user_id:
                return

            asyncio.run(self._handle_message_async(event, say, client))

    async def _handle_message_async(self, event: Any, say: Any, client: Any) -> None:
        """Handle message events asynchronously"""
        try:
            user_id = event.get("user")
            channel_id = event.get("channel")
            thread_ts = event.get("thread_ts") or event.get("ts")
            text = event.get("text", "")

            # Log message details
            self.message_handler.log_message_details(
                user_id, channel_id, thread_ts, text
            )

            # Send initial acknowledgment
            await self.message_handler.send_initial_acknowledgment(
                client, channel_id, thread_ts
            )

            # Process the request with Claude Code
            await self.claude_processor.process_with_claude_code(
                client, channel_id, thread_ts, text, user_id
            )

        except Exception as e:
            error_details = self.message_handler.create_error_details(
                e, "_handle_message_async"
            )

            error_type = error_details["error_type"]
            error_message = error_details["error_message"]
            self.logger.error(f"Error handling message: {error_type}: {error_message}")
            self.logger.error(f"Full traceback:\n{error_details['traceback']}")

            if (
                "client" in locals()
                and "channel_id" in locals()
                and "thread_ts" in locals()
            ):
                await self.message_handler.send_detailed_error_to_slack(
                    client, channel_id, thread_ts, error_details
                )

    def run(self) -> None:
        """Start the Socket Mode handler"""
        try:
            self.logger.info("Starting Slack Socket Mode monitor...")
            slack_app_token = self.config_manager.get_slack_app_token()
            handler = SocketModeHandler(self.app, slack_app_token)
            handler.start()
        except KeyboardInterrupt:
            self.logger.info("Monitoring interrupted by user")
        except Exception as e:
            error_details = self.message_handler.create_error_details(e, "run")

            error_type = error_details["error_type"]
            error_message = error_details["error_message"]
            self.logger.critical(f"Fatal error: {error_type}: {error_message}")
            self.logger.critical(f"Full traceback:\n{error_details['traceback']}")
            sys.exit(1)


def main() -> None:
    """Main entry point"""
    try:
        monitor = SlackSocketMonitor()
        monitor.run()
    except Exception as e:
        # Basic logging for initialization errors since logger might not be set up yet
        error_info = f"Initialization error: {type(e).__name__}: {str(e)}"
        print(error_info)

        # Try to log to file if possible
        try:
            logging_manager = LoggingManager()
            current_log_file = logging_manager.get_current_log_file()

            with open(current_log_file, "a", encoding="utf-8") as f:
                timestamp = f"{datetime.now().isoformat()}"
                f.write(f"{timestamp} - CRITICAL - main - {error_info}\n")
                tb = traceback.format_exc()
                f.write(f"{timestamp} - CRITICAL - main - Traceback:\n{tb}\n")
        except Exception:
            pass  # If logging fails, at least we printed to console

        sys.exit(1)


if __name__ == "__main__":
    main()
