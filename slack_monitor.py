#!/usr/bin/env python3

import os
import sys
import asyncio
import json
from typing import Dict, List, Optional, Any
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
        print(f"Warning: Could not load .env file: {e}")
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

        # Initialize Slack app
        self.app = App(token=SLACK_BOT_TOKEN)

        # Load channel configurations
        self.channel_configs = self._load_channel_configs()

        self.setup_event_handlers()

        print(f"Initialized SlackSocketMonitor")
        print(f"Claude User ID: {CLAUDE_USER_ID}")
        print(
            f"Loaded configurations for {len(self.channel_configs.get('channels', {}))} channels"
        )

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

            print(f"Message detected from user {user_id} in channel {channel_id}")
            print(f"Thread TS: {thread_ts}")
            print(f"Message: {text[:100]}...")

            # Send initial acknowledgment
            await self._send_thread_reply(
                client, channel_id, thread_ts, "指示を確認しました。処理を開始します..."
            )

            # Process the request with Claude Code
            await self._process_with_claude_code(
                client, channel_id, thread_ts, text, user_id
            )

        except Exception as e:
            print(f"Error handling mention: {e}")
            if (
                "client" in locals()
                and "channel_id" in locals()
                and "thread_ts" in locals()
            ):
                await self._send_thread_reply(
                    client, channel_id, thread_ts, f"エラーが発生しました: {str(e)}"
                )

    async def _process_with_claude_code(
        self, client, channel_id: str, thread_ts: str, user_text: str, user_id: str
    ):
        """Process user request with Claude Code SDK"""
        try:
            # Create system prompt
            system_prompt = self._create_system_prompt(thread_ts, user_id)

            # Configure Claude Code options based on channel configuration
            options = self._create_claude_code_options(channel_id, system_prompt)

            print(f"Starting Claude Code query for channel {channel_id}...")

            messages: List[Message] = []

            # Execute Claude Code query
            async for message in query(
                prompt=f"slackに来ているユーザーの指示に従ってください。\n\nユーザーからの指示:\n{user_text}",
                options=options,
            ):
                messages.append(message)

            print(f"Claude Code query completed with {len(messages)} messages")

        except ValueError as e:
            print(f"Configuration error: {e}")
            await self._send_thread_reply(
                client,
                channel_id,
                thread_ts,
                f"設定エラー: {str(e)}",
            )
        except Exception as e:
            print(f"Error processing with Claude Code: {e}")
            await self._send_thread_reply(
                client,
                channel_id,
                thread_ts,
                f"Claude Code処理中にエラーが発生しました: {str(e)}",
            )

    def _create_system_prompt(self, thread_ts: str, user_id: str) -> str:
        """Create system prompt for Claude Code from external file"""
        try:
            with open("system_prompt.md", "r", encoding="utf-8") as f:
                prompt_template = f.read()

            # Replace placeholders
            return prompt_template.format(thread_ts=thread_ts, user_id=user_id)
        except FileNotFoundError:
            print("Warning: system_prompt.md not found, using fallback prompt")
            return f"""
slackに来ているユーザーの指示に従ってください.
対象のスレッドは {thread_ts} です。
ユーザーID: {user_id}
"""
        except Exception as e:
            print(f"Error loading system prompt: {e}")
            return f"""
slackに来ているユーザーの指示に従ってください.
対象のスレッドは {thread_ts} です。
ユーザーID: {user_id}
"""

    def _load_channel_configs(self) -> Dict[str, Any]:
        """Load channel configurations from JSON file"""
        try:
            with open("channel_configs.json", "r", encoding="utf-8") as f:
                configs = json.load(f)
            print("Channel configurations loaded successfully")
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

        print(f"Using config for channel {channel_id}: {config}")
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
            options_dict["permission_prompt_tool_name"] = config["permission_prompt_tool_name"]

        return ClaudeCodeOptions(**options_dict)

    async def _send_thread_reply(
        self, client, channel_id: str, thread_ts: str, text: str
    ):
        """Send a reply to a Slack thread"""
        try:
            # Use the synchronous client method in async context
            response = client.chat_postMessage(
                channel=channel_id, thread_ts=thread_ts, text=text
            )
            print(f"Sent thread reply: {text[:50]}...")
            return response
        except Exception as e:
            print(f"Error sending thread reply: {e}")

    def run(self):
        """Start the Socket Mode handler"""
        try:
            print("Starting Slack Socket Mode monitor...")
            handler = SocketModeHandler(self.app, SLACK_APP_TOKEN)
            handler.start()
        except KeyboardInterrupt:
            print("\nMonitoring interrupted by user")
        except Exception as e:
            print(f"Fatal error: {e}")
            sys.exit(1)


def main():
    """Main entry point"""
    try:
        monitor = SlackSocketMonitor()
        monitor.run()
    except Exception as e:
        print(f"Initialization error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
