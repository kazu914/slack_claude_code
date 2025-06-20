# 🤖 Slack Claude Code Integration

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Slack](https://img.shields.io/badge/Slack-Socket%20Mode-brightgreen.svg)](https://api.slack.com/apis/connections/socket)
[![Claude Code SDK](https://img.shields.io/badge/Claude%20Code-SDK-purple.svg)](https://claude.ai/code)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Slack Socket ModeとClaude Code Python SDKのリアルタイム統合による AI支援システム**

## 🚀 機能

- **🔄 リアルタイム統合**: Socket Modeを使用したSlackとClaude Codeのシームレスな連携
- **🎯 チャンネル固有設定**: Slackチャンネルごとに異なるClaude Code設定が可能
- **📊 スマートツール出力管理**: ツール通知の賢い バッチング機能でノイズを削減
- **🔒 セキュリティファースト**: 環境変数管理による安全なトークンベース認証
- **⚡ 高パフォーマンス**: 包括的エラーハンドリングによる非同期処理
- **🛠️ 開発者フレンドリー**: 完全な型注釈とコード品質ツール統合

## 📋 前提条件

- **Python 3.11+**
- **管理者権限のあるSlackワークスペース**
- **Claude Code CLI** のインストール
- **uv** パッケージマネージャー（推奨）またはpip

## 🛠️ インストール

### 1. リポジトリのクローン

```bash
git clone https://github.com/your-username/slack_claude_code.git
cd slack_claude_code
```

### 2. 依存関係のインストール

#### uv使用（推奨）
```bash
# 仮想環境の自動管理による依存関係インストール
uv sync
```

#### pip使用
```bash
# 仮想環境の作成と有効化
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係のインストール
pip install slack_bolt claude-code-sdk requests
```

### 3. Claude Code CLIのインストール

```bash
npm install -g @anthropic-ai/claude-code
```

## ⚙️ 設定

### 1. 環境変数

サンプル環境ファイルをコピーして、トークンを設定してください：

```bash
cp .env.sample .env
```

`.env`ファイルを実際のトークンで編集：

```bash
# Slack設定
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token-here
SLACK_APP_TOKEN=xapp-your-app-token-here
CLAUDE_USER_ID=your-claude-user-id
```

### 2. Slackアプリの設定

#### Socket Modeの有効化
1. Slackアプリ管理ページに移動
2. サイドバーの「Socket Mode」に移動
3. Socket Modeを有効化

#### アプリレベルトークンの生成
1. 「App Token」セクションに移動
2. 新しいアプリレベルトークンを作成
3. スコープを追加：`connections:write`
4. 生成された`xapp-`トークンを`.env`ファイルにコピー

#### イベントサブスクリプションの設定
以下のイベントを購読していることを確認：
- `app_mention`
- `message.channels`（必要に応じて）

### 3. チャンネル設定

チャンネル設定ファイルを作成：

```bash
cp channel_configs.json.sample channel_configs.json
```

設定例：

```json
{
  "default": {
    "cwd": ".",
    "permission_mode": "bypassPermissions",
    "max_thinking_tokens": 8000
  },
  "channels": {
    "C1234567890": {
      "cwd": "/path/to/specific/project",
      "permission_mode": "requestPermissions",
      "allowed_tools": ["Bash", "Read", "Write", "Edit"],
      "max_turns": 10
    }
  }
}
```

## 🚀 使用方法

### サービスの開始

```bash
# uv使用
uv run python slack_monitor.py

# pip使用
python slack_monitor.py
```

### Slackでの操作

1. **設定されたチャンネルでボットをメンション**
2. **自然言語で指示を与える**
3. **賢いツール出力バッチングで進捗を監視**
4. **Slackスレッドで結果を直接受信**

例：
```
@Claude このコードベースを分析して、改善提案をしてください
```

## 📁 プロジェクト構造

```
slack_claude_code/
├── slack_monitor.py              # メインのSocket Mode監視スクリプト
├── claude_code_message_notifier.py  # スマートツール出力管理
├── message_utils.py              # メッセージ処理ユーティリティ
├── system_prompt.md              # Claude Codeシステムプロンプトテンプレート
├── channel_configs.json          # チャンネル固有設定
├── pyproject.toml               # プロジェクト依存関係と設定
├── SLACK_SETUP.md               # 詳細なセットアップ手順
└── CLAUDE.md                    # Claude Code統合ガイド
```

## 🔧 開発

### コード品質ツール

```bash
# 型チェック
uv run mypy slack_monitor.py

# コードフォーマットとリント
uv run ruff check .
uv run ruff format .

# 変更後の必須チェック
uv tool run ruff check ./slack_monitor.py --fix
```

### 主要コンポーネント

#### SlackSocketMonitorクラス
- Socket Modeイベントハンドリング
- 非同期メッセージ処理
- Claude Code SDK統合

#### ClaudeCodeMessageNotifierクラス
- 賢いツール出力バッチング
- Slack通知ノイズの削減
- 設定可能な通知しきい値

## 🎨 スマート機能

### ツール出力管理
- **バッチ通知**: 10操作ごとにツール使用をまとめて報告
- **混合コンテンツ処理**: ユーザー向けコンテンツの即座表示
- **ノイズ削減**: 重複するツール実行メッセージの除去

### チャンネル柔軟性
- **チャンネル別設定**: Slackチャンネルごとに異なるClaude Code設定
- **権限モード**: バイパスまたは要求許可モードの選択
- **ツール制限**: チャンネルごとの特定ツールの許可/禁止

## 🤝 貢献方法

1. リポジトリをフォーク
2. 機能ブランチを作成（`git checkout -b feature/amazing-feature`）
3. 適切な型注釈で変更を実施
4. コード品質チェックを実行（`uv tool run ruff check . --fix`）
5. 変更をコミット（`git commit -m 'Add amazing feature'`）
6. ブランチにプッシュ（`git push origin feature/amazing-feature`）
7. プルリクエストを開く

## 📝 ライセンス

このプロジェクトはMITライセンスの下でライセンスされています - 詳細は[LICENSE](LICENSE)ファイルを参照してください。

## 🙋‍♀️ サポート

- 📖 **ドキュメント**: 詳細なセットアップ手順は`SLACK_SETUP.md`を確認
- 🐛 **問題報告**: GitHub Issuesでバグを報告
- 💡 **機能要望**: GitHub Issuesで新機能を提案

## 🏆 謝辞

- [Claude Code SDK](https://claude.ai/code)で構築
- [Slack Bolt for Python](https://slack.dev/bolt-python/)により駆動
- 高速Pythonパッケージ管理のため[uv](https://github.com/astral-sh/uv)を使用

---

**シームレスなAI-人間コラボレーションのために❤️で作成**