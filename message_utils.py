#!/usr/bin/env python3
"""
Claude Code SDK Messageオブジェクト用のユーティリティ関数
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
    Claude Code SDKのMessageオブジェクトからテキスト部分を抽出する

    Args:
        message: Claude Code SDKのMessageオブジェクト
        include_tool_info: ツール使用情報を含めるかどうか

    Returns:
        抽出されたテキスト文字列。テキストが含まれていない場合はNone
    """

    if isinstance(message, UserMessage):
        # UserMessageの場合、contentフィールドを適切に処理
        if isinstance(message.content, str):
            return message.content
        elif isinstance(message.content, list):
            # リストの場合はJSONとして返す（tool_resultなど）
            return json.dumps(message.content, ensure_ascii=False, indent=2)
        else:
            return str(message.content)

    elif isinstance(message, AssistantMessage):
        # AssistantMessageの場合、contentはContentBlockのリスト
        text_parts = []

        for content_block in message.content:
            if isinstance(content_block, TextBlock):
                # TextBlockの場合、textフィールドにテキストが含まれている
                text_parts.append(content_block.text)
            elif isinstance(content_block, ToolUseBlock):
                # ToolUseBlockの場合、ツール使用の情報を文字列化
                if include_tool_info:
                    tool_info = f"[Tool: {content_block.name}({content_block.id})]"
                    # inputが重要な場合は追加
                    if content_block.input:
                        input_json = json.dumps(
                            content_block.input, ensure_ascii=False
                        )
                        tool_info += f" Input: {input_json}"
                    text_parts.append(tool_info)
            elif isinstance(content_block, ToolResultBlock):
                # ToolResultBlockの場合、結果の内容を取得
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
        # SystemMessageは通常表示しない（初期化情報など）
        if include_tool_info:
            return f"[System: {message.subtype}]"
        else:
            return None

    elif isinstance(message, ResultMessage):
        # ResultMessageの場合、resultフィールドの内容を返す
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
        # 未知のMessageタイプの場合
        if include_tool_info:
            return f"[Unknown Message Type: {type(message).__name__}]"
        else:
            return None
