#!/usr/bin/env python3
"""
Utility functions for Claude Code SDK Message objects
"""

import json
from typing import Optional

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
        # For UserMessage, properly handle the content field
        if isinstance(message.content, str):
            return message.content
        elif isinstance(message.content, list):
            # For lists, return as JSON (tool_result, etc.)
            return json.dumps(message.content, ensure_ascii=False, indent=2)
        else:
            return str(message.content)

    elif isinstance(message, AssistantMessage):
        # For AssistantMessage, content is a list of ContentBlocks
        text_parts = []

        for content_block in message.content:
            if isinstance(content_block, TextBlock):
                # For TextBlock, text is contained in the text field
                text_parts.append(content_block.text)
            elif isinstance(content_block, ToolUseBlock):
                # For ToolUseBlock, stringify tool usage information
                if include_tool_info:
                    tool_info = f"[Tool: {content_block.name}({content_block.id})]"
                    # Add input if important
                    if content_block.input:
                        input_json = json.dumps(
                            content_block.input, ensure_ascii=False
                        )
                        tool_info += f" Input: {input_json}"
                    text_parts.append(tool_info)
            elif isinstance(content_block, ToolResultBlock):
                # For ToolResultBlock, get result content
                if content_block.content and include_tool_info:
                    if isinstance(content_block.content, str):
                        text_parts.append(f"[Tool Result: {content_block.content}]")
                    else:
                        content_json = json.dumps(
                            content_block.content, ensure_ascii=False
                        )
                        text_parts.append(f"[Tool Result: {content_json}]")

        return "\n".join(text_parts) if text_parts else None

    elif isinstance(message, SystemMessage):
        # SystemMessage is usually not displayed (initialization info, etc.)
        if include_tool_info:
            return f"[System: {message.subtype}]"
        else:
            return None

    elif isinstance(message, ResultMessage):
        # For ResultMessage, return the content of the result field
        if message.result:
            return message.result
        elif include_tool_info:
            return (
                f"[Result: {message.subtype}, Duration: {message.duration_ms}ms, "
                f"Turns: {message.num_turns}]"
            )
        else:
            return None

    else:
        # For unknown Message types
        if include_tool_info:
            return f"[Unknown Message Type: {type(message).__name__}]"
        else:
            return None
