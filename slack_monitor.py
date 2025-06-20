#!/usr/bin/env python3

import os
import sys
import asyncio
import json
import logging
import traceback
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from claude_code_sdk import query, ClaudeCodeOptions, Message


def load_env_file(env_file_path: str = ".env") -> Dict[str, str]:
    """Load environment variables from .env file"""
    env_vars = {}
    try:
        if os.path.exists(env_file_path):
            with open(env_file_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        env_vars[key.strip()] = value.strip("\"'")
    except Exception as e:
        # Use basic logging since the main logger isn't initialized yet
        logging.warning(f"Could not load .env file: {e}")
    return env_vars


# Load environment variables
env_vars = load_env_file()

SLACK_BOT_TOKEN = env_vars.get("SLACK_BOT_TOKEN") or os.getenv("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = env_vars.get("SLACK_APP_TOKEN") or os.getenv("SLACK_APP_TOKEN")
CLAUDE_USER_ID = (
    env_vars.get("CLAUDE_USER_ID") or os.getenv("CLAUDE_USER_ID") or "U0926ED69N0"
)


class SlackSocketMonitor:
    def __init__(self):
        if not SLACK_BOT_TOKEN:
            raise ValueError("SLACK_BOT_TOKEN is required.")
        if not SLACK_APP_TOKEN:
            raise ValueError("SLACK_APP_TOKEN is required.")

        # Setup logging
        self._setup_logging()

        # Initialize Slack app
        self.app = App(token=SLACK_BOT_TOKEN)

        # Load channel configurations
        self.channel_configs = self._load_channel_configs()

        self.setup_event_handlers()

        self.logger.info("Initialized SlackSocketMonitor")
        self.logger.info(f"Claude User ID: {CLAUDE_USER_ID}")
        self.logger.info(
            f"Loaded configurations for {len(self.channel_configs.get('channels', {}))} channels"
        )

    def _setup_logging(self):
        """Setup detailed logging with file output"""
        # Create logs directory if it doesn't exist
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)

        # Configure logger
        self.logger = logging.getLogger("slack_claude_monitor")
        self.logger.setLevel(logging.DEBUG)

        # Remove existing handlers to avoid duplicates
        self.logger.handlers.clear()

        # File handler for detailed logs
        log_file = logs_dir / f"slack_monitor_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)

        # Console handler for basic info
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Detailed formatter for file
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
        )
        file_handler.setFormatter(file_formatter)

        # Simple formatter for console
        console_formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(console_formatter)

        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

        self.logger.info(f"Logging initialized. Log file: {log_file}")

    def setup_event_handlers(self):
        """Setup Slack event handlers"""

        @self.app.event("message")
        def handle_message(event, say, client):
            """Handle messages in monitored channels"""

            # Skip bot messages
            if event.get("bot_id") or event.get("user") == CLAUDE_USER_ID:
                return

            asyncio.run(self._handle_message_async(event, say, client))

    async def _handle_message_async(self, event, say, client):
        """Handle message events asynchronously"""
        try:
            user_id = event.get("user")
            channel_id = event.get("channel")
            thread_ts = event.get("thread_ts") or event.get("ts")
            text = event.get("text", "")

            self.logger.info(
                f"Message detected from user {user_id} in channel {channel_id}"
            )
            self.logger.info(f"Thread TS: {thread_ts}")
            self.logger.debug(f"Message: {text}")

            # Send initial acknowledgment
            await self._send_thread_reply(
                client,
                channel_id,
                thread_ts,
                "指示を確認しました。処理を開始します...",
            )

            # Process the request with Claude Code
            await self._process_with_claude_code(
                client, channel_id, thread_ts, text, user_id
            )

        except Exception as e:
            error_details = {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "traceback": traceback.format_exc(),
                "function": "_handle_message_async",
            }

            self.logger.error(
                f"Error handling message: {error_details['error_type']}: {error_details['error_message']}"
            )
            self.logger.error(f"Full traceback:\n{error_details['traceback']}")

            if (
                "client" in locals()
                and "channel_id" in locals()
                and "thread_ts" in locals()
            ):
                await self._send_detailed_error_to_slack(
                    client, channel_id, thread_ts, error_details
                )

    async def _process_with_claude_code(
        self, client, channel_id: str, thread_ts: str, user_text: str, user_id: str
    ):
        """Process user request with Claude Code SDK"""
        try:
            # Create system prompt
            system_prompt = self._create_system_prompt(thread_ts, user_id, channel_id)

            # Configure Claude Code options based on channel configuration
            options = self._create_claude_code_options(channel_id, system_prompt)

            self.logger.info(f"Starting Claude Code query for channel {channel_id}...")

            messages: List[Message] = []

            # Execute Claude Code query
            async for message in query(
                prompt=f"slackに来ているユーザーの指示に従ってください。\n\nユーザーからの指示:\n{user_text}",
                options=options,
            ):
                self.logger.info(message)
                messages.append(message)

            self.logger.info(
                f"Claude Code query completed with {len(messages)} messages"
            )

            # Send completion notification
            await self._send_claude_code_completion_notification(
                client, channel_id, thread_ts, len(messages)
            )

        except ValueError as e:
            error_details = {
                "error_type": "Configuration Error",
                "error_message": str(e),
                "traceback": traceback.format_exc(),
                "function": "_process_with_claude_code",
                "context": f"Channel: {channel_id}, User: {user_id}",
            }

            self.logger.error(f"Configuration error: {error_details['error_message']}")
            self.logger.error(f"Full traceback:\n{error_details['traceback']}")
            await self._send_detailed_error_to_slack(
                client, channel_id, thread_ts, error_details
            )
        except Exception as e:
            error_details = {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "traceback": traceback.format_exc(),
                "function": "_process_with_claude_code",
                "context": f"Channel: {channel_id}, User: {user_id}",
            }

            self.logger.error(
                f"Error processing with Claude Code: {error_details['error_type']}: {error_details['error_message']}"
            )
            self.logger.error(f"Full traceback:\n{error_details['traceback']}")
            await self._send_detailed_error_to_slack(
                client, channel_id, thread_ts, error_details
            )

    def _create_system_prompt(
        self, thread_ts: str, user_id: str, channel_id: str
    ) -> str:
        """Create system prompt for Claude Code from external file"""
        try:
            with open("system_prompt.md", "r", encoding="utf-8") as f:
                prompt_template = f.read()

            # Replace placeholders
            return prompt_template.format(
                thread_ts=thread_ts, user_id=user_id, channel_id=channel_id
            )
        except FileNotFoundError:
            self.logger.warning("system_prompt.md not found, using fallback prompt")
            return f"""
slackに来ているユーザーの指示に従ってください.
対象のスレッドは {thread_ts} です。
ユーザーID: {user_id}
チャンネルID: {channel_id}
"""
        except Exception as e:
            self.logger.error(f"Error loading system prompt: {e}")
            return f"""
slackに来ているユーザーの指示に従ってください.
対象のスレッドは {thread_ts} です。
ユーザーID: {user_id}
チャンネルID: {channel_id}
"""

    def _load_channel_configs(self) -> Dict[str, Any]:
        """Load channel configurations from JSON file"""
        try:
            with open("channel_configs.json", "r", encoding="utf-8") as f:
                configs = json.load(f)
            self.logger.info("Channel configurations loaded successfully")
            return configs
        except FileNotFoundError:
            raise FileNotFoundError(
                "channel_configs.json is required but not found. "
                "Please create the configuration file before starting the application."
            )
        except json.JSONDecodeError as e:
            raise ValueError(f"Error parsing channel_configs.json: {e}")
        except Exception as e:
            raise RuntimeError(f"Error loading channel configurations: {e}")

    def _get_channel_config(self, channel_id: str) -> Dict[str, Any]:
        """Get configuration for a specific channel"""
        default_config = self.channel_configs.get("default", {})
        channel_specific = self.channel_configs.get("channels", {}).get(channel_id, {})

        # Merge configurations (channel-specific overrides default)
        config = {**default_config, **channel_specific}

        self.logger.debug(f"Using config for channel {channel_id}: {config}")
        return config

    def _create_claude_code_options(
        self, channel_id: str, system_prompt: str
    ) -> ClaudeCodeOptions:
        """Create ClaudeCodeOptions based on channel configuration"""
        config = self._get_channel_config(channel_id)

        # Validate required configuration values
        if not config.get("cwd"):
            raise ValueError(
                f"Missing required 'cwd' configuration for channel {channel_id}"
            )
        if not config.get("permission_mode"):
            raise ValueError(
                f"Missing required 'permission_mode' configuration for channel {channel_id}"
            )

        # Build options dictionary with non-None values
        options_dict = {
            "system_prompt": system_prompt,
            "cwd": Path(config["cwd"]),
            "permission_mode": config["permission_mode"],
        }

        # Add all ClaudeCodeOptions parameters if they are specified
        if config.get("allowed_tools") is not None:
            options_dict["allowed_tools"] = config["allowed_tools"]
        if config.get("max_thinking_tokens") is not None:
            options_dict["max_thinking_tokens"] = config["max_thinking_tokens"]
        if config.get("append_system_prompt"):
            options_dict["append_system_prompt"] = config["append_system_prompt"]
        if config.get("mcp_tools") is not None:
            options_dict["mcp_tools"] = config["mcp_tools"]
        if config.get("mcp_servers") is not None:
            options_dict["mcp_servers"] = config["mcp_servers"]
        if config.get("continue_conversation") is not None:
            options_dict["continue_conversation"] = config["continue_conversation"]
        if config.get("resume"):
            options_dict["resume"] = config["resume"]
        if config.get("max_turns") is not None:
            options_dict["max_turns"] = config["max_turns"]
        if config.get("disallowed_tools") is not None:
            options_dict["disallowed_tools"] = config["disallowed_tools"]
        if config.get("model"):
            options_dict["model"] = config["model"]
        if config.get("permission_prompt_tool_name"):
            options_dict["permission_prompt_tool_name"] = config[
                "permission_prompt_tool_name"
            ]

        return ClaudeCodeOptions(**options_dict)

    def _add_auto_send_prefix(self, message: str) -> str:
        """Add auto-send prefix to distinguish Python-generated messages from Claude's messages"""
        return f"【自動送信】{message}"

    async def _send_claude_code_completion_notification(
        self, client, channel_id: str, thread_ts: str, message_count: int
    ):
        """Send notification when Claude Code processing is completed"""
        try:
            completion_message = "✅ Claude Code処理が完了しました"

            await self._send_thread_reply(
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

    async def _send_thread_reply(
        self, client, channel_id: str, thread_ts: str, text: str
    ):
        """Send a reply to a Slack thread with auto-send prefix"""
        try:
            # Add auto-send prefix to all messages sent through this function
            prefixed_text = self._add_auto_send_prefix(text)

            # Use the synchronous client method in async context
            response = client.chat_postMessage(
                channel=channel_id, thread_ts=thread_ts, text=prefixed_text
            )
            self.logger.debug(f"Sent thread reply: {text[:50]}...")
            return response
        except Exception as e:
            self.logger.error(f"Error sending thread reply: {e}")

    async def _send_detailed_error_to_slack(
        self, client, channel_id: str, thread_ts: str, error_details: Dict[str, str]
    ):
        """Send detailed error information to Slack"""
        try:
            # Create a user-friendly error message
            error_message = f"""🚨 **エラーが発生しました**

**エラータイプ**: {error_details['error_type']}
**エラーメッセージ**: {error_details['error_message']}
**発生場所**: {error_details['function']}

**詳細情報**:
```
{error_details.get('context', 'コンテキスト情報なし')}
```

詳細なスタックトレースはログファイルに記録されています。
ログファイル: `logs/slack_monitor_{datetime.now().strftime('%Y%m%d')}.log`"""

            # Send to Slack through _send_thread_reply (auto-prefix will be added)
            response = await self._send_thread_reply(
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
                simple_error = f"エラーが発生しました: {error_details['error_type']} - {error_details['error_message']}"
                await self._send_thread_reply(
                    client,
                    channel_id,
                    thread_ts,
                    simple_error,
                )
            except Exception as fallback_error:
                self.logger.critical(
                    f"Failed to send even simple error message: {fallback_error}"
                )

    def run(self):
        """Start the Socket Mode handler"""
        try:
            self.logger.info("Starting Slack Socket Mode monitor...")
            handler = SocketModeHandler(self.app, SLACK_APP_TOKEN)
            handler.start()
        except KeyboardInterrupt:
            self.logger.info("Monitoring interrupted by user")
        except Exception as e:
            error_details = {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "traceback": traceback.format_exc(),
                "function": "run",
            }

            self.logger.critical(
                f"Fatal error: {error_details['error_type']}: {error_details['error_message']}"
            )
            self.logger.critical(f"Full traceback:\n{error_details['traceback']}")
            sys.exit(1)


def main():
    """Main entry point"""
    try:
        monitor = SlackSocketMonitor()
        monitor.run()
    except Exception as e:
        # Basic logging for initialization errors since logger might not be set up yet
        error_info = f"Initialization error: {type(e).__name__}: {str(e)}"
        logging.critical(error_info)

        # Try to log to file if possible
        try:
            logs_dir = Path("logs")
            logs_dir.mkdir(exist_ok=True)
            log_file = (
                logs_dir / f"slack_monitor_{datetime.now().strftime('%Y%m%d')}.log"
            )

            with open(log_file, "a", encoding="utf-8") as f:
                f.write(
                    f"{datetime.now().isoformat()} - CRITICAL - main - {error_info}\n"
                )
                f.write(
                    f"{datetime.now().isoformat()} - CRITICAL - main - Traceback:\n{traceback.format_exc()}\n"
                )
        except Exception:
            pass  # If logging fails, at least we printed to console

        sys.exit(1)


if __name__ == "__main__":
    main()
