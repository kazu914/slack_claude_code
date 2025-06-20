#!/usr/bin/env python3
"""
Claude Code メッセージ通知制御クラス

Tools出力の頻繁な通知を制御し、適切なタイミングでSlackに通知を行う
"""

from typing import List, Optional

from claude_code_sdk.types import (
    AssistantMessage,
    Message,
    ToolResultBlock,
    ToolUseBlock,
)

from message_utils import extract_message_text


class ClaudeCodeMessageNotifier:
    """
    Claude Codeからのメッセージを制御し、tools出力の通知頻度を調整するクラス

    Tools出力は即座に通知せず、以下の条件で通知を行う：
    - Tools以外の出力が発生したとき
    - Toolsの出力が連続で10回続いたとき
    """

    def __init__(self) -> None:
        """初期化"""
        self.tools_count = 0

    def process_message(self, message: Message) -> List[str]:
        """
        メッセージを処理し、Slackに送信すべきメッセージリストを返す

        Args:
            message: Claude Code SDKのMessageオブジェクト

        Returns:
            List[str]: Slackに送信すべきメッセージのリスト
        """
        message_text = extract_message_text(message)

        if self._is_tools_message(message, message_text):
            return self._handle_tools_message()
        else:
            return self._handle_non_tools_message(message_text)

    def _handle_tools_message(self) -> List[str]:
        """Tools メッセージを処理"""
        self.tools_count += 1

        if self.tools_count % 10 == 0:
            # 10の倍数になった場合、通知して リセット
            count = self.tools_count
            self.tools_count = 0
            return [f"{count}回toolsを使用しました"]

        # まだ通知しない
        return []

    def _handle_non_tools_message(self, message_text: Optional[str]) -> List[str]:
        """Tools以外のメッセージを処理"""
        messages_to_send = []

        # 蓄積されたtools通知がある場合、先に送信
        if self.tools_count > 0:
            messages_to_send.append(f"{self.tools_count}回toolsを使用しました")
            self.tools_count = 0

        # 現在のメッセージがテキストを含む場合、追加
        if message_text:
            messages_to_send.append(message_text)

        return messages_to_send

    def _is_tools_message(
        self, message: Message, message_text: Optional[str]
    ) -> bool:
        """
        メッセージがtools出力かどうかを判定

        Args:
            message: Claude Code SDKのMessageオブジェクト
            message_text: 抽出されたメッセージテキスト

        Returns:
            bool: Tools出力の場合True
        """
        # AssistantMessageでToolブロックが含まれる場合は常にtools
        if isinstance(message, AssistantMessage):
            has_tool_blocks = any(
                isinstance(block, (ToolUseBlock, ToolResultBlock))
                for block in message.content
            )
            if has_tool_blocks:
                return True

        # UserMessageでcontentがlistの場合（tool_resultなど）
        if hasattr(message, 'content') and isinstance(message.content, list):
            return True

        # メッセージテキストがJSONデータの場合
        if message_text and (
            message_text.strip().startswith('[') or
            message_text.strip().startswith('{') or
            '"type":' in message_text or
            '"tool_use_id":' in message_text
        ):
            return True

        # テキストがない場合、toolsまたはメタデータの可能性が高い
        if message_text is None:
            return True

        # 通常のテキストメッセージ
        return False

    def get_pending_tools_notification(self) -> Optional[str]:
        """
        未送信のtools通知があれば取得する（処理完了時などに使用）

        Returns:
            Optional[str]: 未送信のtools通知メッセージ。なければNone
        """
        if self.tools_count > 0:
            count = self.tools_count
            self.tools_count = 0
            return f"{count}回toolsを使用しました"
        return None

    def reset_count(self) -> None:
        """Toolsカウントをリセット"""
        self.tools_count = 0

    @property
    def current_tools_count(self) -> int:
        """現在のtoolsカウント数を取得"""
        return self.tools_count
