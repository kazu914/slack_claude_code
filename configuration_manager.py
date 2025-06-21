#!/usr/bin/env python3
"""
Configuration Manager for Slack Claude Code Integration

Handles environment variables, channel configurations, and system prompts
"""

import json
import logging
import os
from typing import Any, Dict, Optional


class ConfigurationManager:
    """
    Manages all configuration aspects of the Slack Claude Code integration

    Responsibilities:
    - Load and manage environment variables
    - Load and provide channel-specific configurations
    - Load and format system prompts
    """

    def __init__(self, env_file_path: str = ".env") -> None:
        """
        Initialize configuration manager

        Args:
            env_file_path: Path to environment file
        """
        # Set up basic logging for this class first
        self.logger = logging.getLogger(self.__class__.__name__)

        self.env_vars = self._load_env_file(env_file_path)
        self.channel_configs = self._load_channel_configs()

    def _load_env_file(self, env_file_path: str) -> Dict[str, str]:
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

    def _load_channel_configs(self) -> Dict[str, Any]:
        """Load channel configurations from JSON file"""
        try:
            with open("channel_configs.json", "r", encoding="utf-8") as f:
                configs = json.load(f)
            self.logger.info("Channel configurations loaded successfully")
            return configs  # type: ignore
        except FileNotFoundError:
            raise FileNotFoundError(
                "channel_configs.json is required but not found. "
                "Please create the configuration file before starting the application."
            )
        except json.JSONDecodeError as e:
            raise ValueError(f"Error parsing channel_configs.json: {e}")
        except Exception as e:
            raise RuntimeError(f"Error loading channel configurations: {e}")

    def get_env_var(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get environment variable value

        Args:
            key: Environment variable key
            default: Default value if not found

        Returns:
            Environment variable value
        """
        return self.env_vars.get(key) or os.getenv(key) or default

    def get_slack_bot_token(self) -> str:
        """Get Slack Bot Token"""
        token = self.get_env_var("SLACK_BOT_TOKEN")
        if not token:
            raise ValueError("SLACK_BOT_TOKEN is required.")
        return token

    def get_slack_app_token(self) -> str:
        """Get Slack App Token"""
        token = self.get_env_var("SLACK_APP_TOKEN")
        if not token:
            raise ValueError("SLACK_APP_TOKEN is required.")
        return token

    def get_claude_user_id(self) -> str:
        """Get Claude User ID"""
        return self.get_env_var("CLAUDE_USER_ID", "U0926ED69N0") or "U0926ED69N0"

    def get_channel_config(self, channel_id: str) -> Dict[str, Any]:
        """
        Get configuration for a specific channel

        Args:
            channel_id: Slack channel ID

        Returns:
            Channel configuration dictionary
        """
        default_config = self.channel_configs.get("default", {})
        channel_specific = self.channel_configs.get("channels", {}).get(channel_id, {})

        # Merge configurations (channel-specific overrides default)
        config = {**default_config, **channel_specific}

        self.logger.debug(f"Using config for channel {channel_id}: {config}")
        return config

    def get_channels_count(self) -> int:
        """Get the number of configured channels"""
        return len(self.channel_configs.get("channels", {}))

    def create_system_prompt(
        self, thread_ts: str, user_id: str, channel_id: str
    ) -> str:
        """
        Create system prompt for Claude Code from external file

        Args:
            thread_ts: Slack thread timestamp
            user_id: Slack user ID
            channel_id: Slack channel ID

        Returns:
            Formatted system prompt
        """
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
Follow the user instructions received in Slack.
Target thread is {thread_ts}.
User ID: {user_id}
Channel ID: {channel_id}
"""
        except Exception as e:
            self.logger.error(f"Error loading system prompt: {e}")
            return f"""
Follow the user instructions received in Slack.
Target thread is {thread_ts}.
User ID: {user_id}
Channel ID: {channel_id}
"""

    def validate_channel_config(self, channel_id: str) -> None:
        """
        Validate channel configuration

        Args:
            channel_id: Slack channel ID

        Raises:
            ValueError: If configuration is invalid
        """
        config = self.get_channel_config(channel_id)

        if not config.get("cwd"):
            msg = f"Missing required 'cwd' configuration for channel {channel_id}"
            raise ValueError(msg)
        if not config.get("permission_mode"):
            msg = (
                f"Missing required 'permission_mode' configuration for "
                f"channel {channel_id}"
            )
            raise ValueError(msg)
