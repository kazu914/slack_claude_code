#!/usr/bin/env python3
"""
Claude Code SDK Messageオブジェクトの構造調査とテキスト抽出テスト
"""

import asyncio
import json
from pathlib import Path
from typing import Optional

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
        # UserMessageの場合、直接contentフィールドにテキストが含まれている
        # ただし、contentがlistの場合もあるため、適切に処理する
        if isinstance(message.content, str):
            return message.content
        elif isinstance(message.content, list):
            return json.dumps(message.content, ensure_ascii=False)
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
                tool_info = f"[Tool: {content_block.name}({content_block.id})]"
                text_parts.append(tool_info)
            elif isinstance(content_block, ToolResultBlock):
                # ToolResultBlockの場合、結果の内容を取得
                if content_block.content:
                    if isinstance(content_block.content, str):
                        text_parts.append(f"[Tool Result: {content_block.content}]")
                    else:
                        text_parts.append(
                            f"[Tool Result: {json.dumps(content_block.content)}]"
                        )

        return "\n".join(text_parts) if text_parts else None

    elif isinstance(message, SystemMessage):
        # SystemMessageの場合、dataフィールドから情報を抽出
        return f"[System: {message.subtype}] {json.dumps(message.data)}"

    elif isinstance(message, ResultMessage):
        # ResultMessageの場合、resultフィールドまたは基本情報を返す
        if message.result:
            return message.result
        else:
            return (
                f"[Result: {message.subtype}, Duration: {message.duration_ms}ms, "
                f"Turns: {message.num_turns}]"
            )

    else:
        # 未知のMessageタイプの場合
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
    for attr_name in dir(message):
        if not attr_name.startswith("_"):  # プライベート属性は除外
            try:
                attr_value = getattr(message, attr_name)
                if not callable(attr_value):  # メソッドは除外
                    analysis["attributes"][attr_name] = {
                        "type": type(attr_value).__name__,
                        "value": attr_value,
                    }
            except Exception as e:
                analysis["attributes"][attr_name] = {"error": str(e)}

    return analysis


async def test_message_structure():
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


async def demonstrate_text_extraction():
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
