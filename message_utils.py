#!/usr/bin/env python3
"""
Utility functions for Claude Code SDK Message objects
"""

import json
from typing import Any, Optional

from claude_code_sdk.types import (
    AssistantMessage,
    Message,
    ResultMessage,
    SystemMessage,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
)


def extract_message_text(
    message: Message, include_tool_info: bool = False
) -> Optional[str]:
    """
    Extract text portion from Claude Code SDK Message object

    Args:
        message: Claude Code SDK Message object
        include_tool_info: Whether to include tool usage information

    Returns:
        Extracted text string. None if no text is contained
    """
    if isinstance(message, UserMessage):
        return _extract_user_message_text(message)
    elif isinstance(message, AssistantMessage):
        return _extract_assistant_message_text(message, include_tool_info)
    elif isinstance(message, SystemMessage):
        return _extract_system_message_text(message, include_tool_info)
    elif isinstance(message, ResultMessage):
        return _extract_result_message_text(message, include_tool_info)
    else:
        return _extract_unknown_message_text(message, include_tool_info)


def _extract_user_message_text(message: UserMessage) -> Optional[str]:
    """
    Extract text from UserMessage

    Args:
        message: UserMessage object

    Returns:
        Extracted text or None
    """
    if isinstance(message.content, str):
        return message.content
    elif isinstance(message.content, list):
        # For lists, return as JSON (tool_result, etc.)
        return json.dumps(message.content, ensure_ascii=False, indent=2)
    else:
        return str(message.content)


def _extract_assistant_message_text(
    message: AssistantMessage, include_tool_info: bool
) -> Optional[str]:
    """
    Extract text from AssistantMessage

    Args:
        message: AssistantMessage object
        include_tool_info: Whether to include tool information

    Returns:
        Extracted text or None
    """
    text_parts = []

    for content_block in message.content:
        block_text = _extract_content_block_text(content_block, include_tool_info)
        if block_text:
            text_parts.append(block_text)

    return "\n".join(text_parts) if text_parts else None


def _extract_content_block_text(
    content_block: Any, include_tool_info: bool
) -> Optional[str]:
    """
    Extract text from a single content block

    Args:
        content_block: Content block object
        include_tool_info: Whether to include tool information

    Returns:
        Extracted text or None
    """
    if isinstance(content_block, TextBlock):
        return content_block.text
    elif isinstance(content_block, ToolUseBlock):
        return _extract_tool_use_text(content_block, include_tool_info)
    elif isinstance(content_block, ToolResultBlock):
        return _extract_tool_result_text(content_block, include_tool_info)
    return None


def _extract_tool_use_text(
    tool_block: ToolUseBlock, include_tool_info: bool
) -> Optional[str]:
    """
    Extract text from ToolUseBlock

    Args:
        tool_block: ToolUseBlock object
        include_tool_info: Whether to include tool information

    Returns:
        Tool information text or None
    """
    if not include_tool_info:
        return None

    tool_info = f"[Tool: {tool_block.name}({tool_block.id})]"
    # Add input if important
    if tool_block.input:
        input_json = json.dumps(tool_block.input, ensure_ascii=False)
        tool_info += f" Input: {input_json}"
    return tool_info


def _extract_tool_result_text(
    result_block: ToolResultBlock, include_tool_info: bool
) -> Optional[str]:
    """
    Extract text from ToolResultBlock

    Args:
        result_block: ToolResultBlock object
        include_tool_info: Whether to include tool information

    Returns:
        Tool result text or None
    """
    if not (result_block.content and include_tool_info):
        return None

    if isinstance(result_block.content, str):
        return f"[Tool Result: {result_block.content}]"
    else:
        content_json = json.dumps(result_block.content, ensure_ascii=False)
        return f"[Tool Result: {content_json}]"


def _extract_system_message_text(
    message: SystemMessage, include_tool_info: bool
) -> Optional[str]:
    """
    Extract text from SystemMessage

    Args:
        message: SystemMessage object
        include_tool_info: Whether to include tool information

    Returns:
        System message text or None
    """
    if include_tool_info:
        return f"[System: {message.subtype}]"
    else:
        return None


def _extract_result_message_text(
    message: ResultMessage, include_tool_info: bool
) -> Optional[str]:
    """
    Extract text from ResultMessage

    Args:
        message: ResultMessage object
        include_tool_info: Whether to include tool information

    Returns:
        Result message text or None
    """
    if message.result:
        return message.result
    elif include_tool_info:
        return (
            f"[Result: {message.subtype}, Duration: {message.duration_ms}ms, "
            f"Turns: {message.num_turns}]"
        )
    else:
        return None


def _extract_unknown_message_text(
    message: Message, include_tool_info: bool
) -> Optional[str]:
    """
    Extract text from unknown message types

    Args:
        message: Unknown message object
        include_tool_info: Whether to include tool information

    Returns:
        Unknown message type text or None
    """
    if include_tool_info:
        return f"[Unknown Message Type: {type(message).__name__}]"
    else:
        return None
