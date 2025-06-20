# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

このプロジェクトはSlackのSocket Modeを使用してClaude Code Python SDKと連携するリアルタイム監視システムです。SlackのメッセージイベントをSocket Modeで受信し、Claude Code SDKを使用してユーザーの指示を処理します。

## 主要なファイル構成

- `slack_monitor.py`: メインのSocket Mode監視スクリプト
- `system_prompt.md`: Claude Code用のシステムプロンプト設定
- `channel_configs.json`: チャンネル別のClaude Code設定
- `pyproject.toml`: uvプロジェクト設定ファイル（Python依存関係管理）
- `uv.lock`: uv依存関係ロックファイル
- `SLACK_SETUP.md`: セットアップ手順書
- `.env.sample`: 環境変数テンプレート（実際の`.env`ファイルはリポジトリに含まれない）

## 開発・実行コマンド

```bash
# 依存関係のインストール（仮想環境を自動作成・管理）
uv sync

# 環境変数の設定
cp .env.sample .env
# .envファイルを編集してトークンを設定

# 実行（uvが仮想環境を自動管理）
uv run python slack_monitor.py
```

### 開発時の追加コマンド

```bash
# コードの静的解析
uv run mypy slack_monitor.py

# コードのフォーマット・リント
uv run ruff check .
uv run ruff format .
```

### 改修後の必須チェック

**重要**: コード改修後は必ず以下のコマンドを実行してエラーがないことを確認してください：

```bash
# slack_monitor.pyの改修後チェック（必須）
uv tool run ruff check ./slack_monitor.py --fix
```

## 必要な環境変数

- `SLACK_BOT_TOKEN`: Slack Bot User OAuth Token (xoxb-)
- `SLACK_APP_TOKEN`: Slack App-level Token (xapp-)
- `CLAUDE_USER_ID`: Claude用のユーザーID

## アーキテクチャ

### SlackSocketMonitor クラス
- Socket Modeでリアルタイムなイベント受信
- メッセージイベントの非同期処理
- Claude Code SDKとの統合

### 主要な処理フロー
1. Slackからメッセージイベントを受信  
2. ユーザーの指示を確認し、初期応答を送信
3. Claude Code SDKを使用してユーザーの指示を処理
4. 処理結果をSlackスレッドに返信

### Claude Code統合設定
- 権限モード: `bypassPermissions`
- 日本語でのコミュニケーション
- 進捗報告機能付き
- 作業ディレクトリは実行時に設定可能
- システムプロンプトは`system_prompt.md`から動的に読み込み
- チャンネル別設定は`channel_configs.json`で管理

## チャンネル別設定

`channel_configs.json`ファイルでSlackチャンネルごとに異なるClaude Code設定を指定できます。

### 設定例

```json
{
  "default": {
    "cwd": ".",
    "permission_mode": "bypassPermissions",
    "allowed_tools": [],
    "max_thinking_tokens": 8000,
    "append_system_prompt": null,
    "mcp_tools": [],
    "mcp_servers": {},
    "continue_conversation": false,
    "resume": null,
    "max_turns": null,
    "disallowed_tools": [],
    "model": null,
    "permission_prompt_tool_name": null
  },
  "channels": {
    "CHANNEL_ID_1": {
      "cwd": "/path/to/project1",
      "permission_mode": "requestPermissions",
      "allowed_tools": ["Bash", "Read", "Write", "Edit"],
      "max_thinking_tokens": 4000,
      "append_system_prompt": "Additional instructions for this channel",
      "mcp_tools": ["slack"],
      "mcp_servers": {},
      "continue_conversation": true,
      "resume": null,
      "max_turns": 10,
      "disallowed_tools": ["WebFetch"],
      "model": "claude-3-5-sonnet-20241022",
      "permission_prompt_tool_name": "custom_permission_tool"
    },
    "CHANNEL_ID_2": {
      "cwd": "/path/to/project2",
      "permission_mode": "bypassPermissions"
    }
  }
}
```

### 設定項目

#### 必須項目
- `cwd`: 作業ディレクトリ
- `permission_mode`: 権限モード (`bypassPermissions` または `requestPermissions`)

#### オプション項目
- `allowed_tools`: 使用可能なツールのリスト（例: `["Bash", "Read", "Write"]`）
- `max_thinking_tokens`: 思考トークンの最大数（デフォルト: 8000）
- `append_system_prompt`: システムプロンプトに追加するテキスト
- `mcp_tools`: MCPツールのリスト
- `mcp_servers`: MCPサーバーの設定
- `continue_conversation`: 会話の継続設定（boolean）
- `resume`: 再開するセッションID
- `max_turns`: 最大ターン数
- `disallowed_tools`: 使用禁止ツールのリスト
- `model`: 使用するClaudeモデル
- `permission_prompt_tool_name`: 権限プロンプトツール名

チャンネル固有の設定がない場合は`default`設定が使用されます。
