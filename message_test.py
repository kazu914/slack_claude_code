#!/usr/bin/env python3
"""
Claude Code SDK Messageオブジェクトの構造調査とテキスト抽出テスト
"""

import asyncio
import json
from pathlib import Path
from typing import Any, Optional

from claude_code_sdk import ClaudeCodeOptions, Message, query
from claude_code_sdk.types import (
    AssistantMessage,
    ResultMessage,
    SystemMessage,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
)


def extract_text_from_message(message: Message) -> Optional[str]:
    """
    Claude Code SDKのMessageオブジェクトからテキスト部分を抽出する

    Args:
        message: Claude Code SDKのMessageオブジェクト

    Returns:
        抽出されたテキスト文字列。テキストが含まれていない場合はNone
    """
    if isinstance(message, UserMessage):
        return _extract_user_message_content(message)
    elif isinstance(message, AssistantMessage):
        return _extract_assistant_message_content(message)
    elif isinstance(message, SystemMessage):
        return _extract_system_message_content(message)
    elif isinstance(message, ResultMessage):
        return _extract_result_message_content(message)
    else:
        return _extract_unknown_message_content(message)


def _extract_user_message_content(message: UserMessage) -> Optional[str]:
    """
    UserMessageからテキストを抽出

    Args:
        message: UserMessage object

    Returns:
        抽出されたテキスト
    """
    if isinstance(message.content, str):
        return message.content
    elif isinstance(message.content, list):
        return json.dumps(message.content, ensure_ascii=False)
    else:
        return str(message.content)


def _extract_assistant_message_content(message: AssistantMessage) -> Optional[str]:
    """
    AssistantMessageからテキストを抽出

    Args:
        message: AssistantMessage object

    Returns:
        抽出されたテキスト
    """
    text_parts = []

    for content_block in message.content:
        block_text = _extract_content_block(content_block)
        if block_text:
            text_parts.append(block_text)

    return "\n".join(text_parts) if text_parts else None


def _extract_content_block(content_block: Any) -> Optional[str]:
    """
    コンテンツブロックからテキストを抽出

    Args:
        content_block: コンテンツブロック

    Returns:
        抽出されたテキスト
    """
    if isinstance(content_block, TextBlock):
        return content_block.text
    elif isinstance(content_block, ToolUseBlock):
        return f"[Tool: {content_block.name}({content_block.id})]"
    elif isinstance(content_block, ToolResultBlock):
        return _extract_tool_result_content(content_block)
    return None


def _extract_tool_result_content(content_block: ToolResultBlock) -> Optional[str]:
    """
    ToolResultBlockからテキストを抽出

    Args:
        content_block: ToolResultBlock

    Returns:
        抽出されたテキスト
    """
    if not content_block.content:
        return None

    if isinstance(content_block.content, str):
        return f"[Tool Result: {content_block.content}]"
    else:
        return f"[Tool Result: {json.dumps(content_block.content)}]"


def _extract_system_message_content(message: SystemMessage) -> str:
    """
    SystemMessageからテキストを抽出

    Args:
        message: SystemMessage object

    Returns:
        抽出されたテキスト
    """
    return f"[System: {message.subtype}] {json.dumps(message.data)}"


def _extract_result_message_content(message: ResultMessage) -> str:
    """
    ResultMessageからテキストを抽出

    Args:
        message: ResultMessage object

    Returns:
        抽出されたテキスト
    """
    if message.result:
        return message.result
    else:
        return (
            f"[Result: {message.subtype}, Duration: {message.duration_ms}ms, "
            f"Turns: {message.num_turns}]"
        )


def _extract_unknown_message_content(message: Message) -> str:
    """
    未知のメッセージタイプからテキストを抽出

    Args:
        message: Message object

    Returns:
        抽出されたテキスト
    """
    return f"[Unknown Message Type: {type(message).__name__}]"


def analyze_message_structure(message: Message) -> dict:
    """
    Messageオブジェクトの詳細な構造を分析する

    Args:
        message: Claude Code SDKのMessageオブジェクト

    Returns:
        メッセージの構造情報を含む辞書
    """
    analysis = {
        "message_type": type(message).__name__,
        "attributes": {},
        "text_content": extract_text_from_message(message),
    }

    # 各属性を詳細に分析
    _analyze_message_attributes(message, analysis)

    return analysis


def _analyze_message_attributes(message: Message, analysis: dict) -> None:
    """
    メッセージの属性を分析

    Args:
        message: Message object
        analysis: 分析結果を格納する辞書
    """
    for attr_name in dir(message):
        if not attr_name.startswith("_"):  # プライベート属性は除外
            _analyze_single_attribute(message, attr_name, analysis)


def _analyze_single_attribute(message: Message, attr_name: str, analysis: dict) -> None:
    """
    単一の属性を分析

    Args:
        message: Message object
        attr_name: 属性名
        analysis: 分析結果を格納する辞書
    """
    try:
        attr_value = getattr(message, attr_name)
        if not callable(attr_value):  # メソッドは除外
            analysis["attributes"][attr_name] = {
                "type": type(attr_value).__name__,
                "value": attr_value,
            }
    except Exception as e:
        analysis["attributes"][attr_name] = {"error": str(e)}


async def test_message_structure() -> None:
    """
    簡単なクエリを実行してMessageオブジェクトの構造をテストする
    """

    print("=== Claude Code SDK Message構造調査 ===\n")

    # テスト用のオプション設定
    options = ClaudeCodeOptions(
        cwd=Path.cwd(),
        permission_mode="bypassPermissions",
        system_prompt="簡潔に日本語で応答してください。",
    )

    # 簡単なテストクエリ
    test_prompt = "こんにちは。現在の時刻を教えてください。"

    print(f"テストプロンプト: {test_prompt}\n")
    print("=== 受信したメッセージの分析 ===\n")

    message_count = 0

    try:
        async for message in query(prompt=test_prompt, options=options):
            message_count += 1

            print(f"--- Message {message_count} ---")
            print(f"Raw Message Object: {message}")
            print(f"Message Type: {type(message).__name__}")

            # テキスト抽出のテスト
            extracted_text = extract_text_from_message(message)
            print(f"Extracted Text: {extracted_text}")

            # 詳細構造分析
            analysis = analyze_message_structure(message)
            print("Detailed Analysis:")
            print(json.dumps(analysis, indent=2, ensure_ascii=False, default=str))

            print("\n" + "=" * 50 + "\n")

    except Exception as e:
        print(f"エラーが発生しました: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()

    print(f"合計 {message_count} 個のメッセージを受信しました。")


async def demonstrate_text_extraction() -> None:
    """
    実際のユースケースでのテキスト抽出のデモンストレーション
    """

    print("=== テキスト抽出デモンストレーション ===\n")

    options = ClaudeCodeOptions(
        cwd=Path.cwd(),
        permission_mode="bypassPermissions",
        system_prompt="簡潔に日本語で応答してください。",
    )

    # より複雑なテストクエリ（ツール使用を含む可能性がある）
    test_prompt = "現在のディレクトリの内容を確認して、何があるか教えてください。"

    print(f"テストプロンプト: {test_prompt}\n")
    print("=== 抽出されたテキスト ===\n")

    all_texts = []

    try:
        async for message in query(prompt=test_prompt, options=options):
            extracted_text = extract_text_from_message(message)
            if extracted_text:
                print(f"[{type(message).__name__}] {extracted_text}")
                all_texts.append(extracted_text)

        print("\n=== 全テキストの結合 ===")
        combined_text = "\n".join(all_texts)
        print(combined_text)

    except Exception as e:
        print(f"エラーが発生しました: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_message_structure())
    print("\n" + "=" * 80 + "\n")
    asyncio.run(demonstrate_text_extraction())
