# Slack Socket Mode 連携セットアップ手順

## 概要
Bolt for PythonとClaude Code Python SDKを使用したリアルタイム連携を行います。

## セットアップ手順

### 1. 依存関係のインストール

```bash
# Python仮想環境の作成（推奨）
python3 -m venv venv
source venv/bin/activate

# 必要なパッケージのインストール
pip install -r requirements.txt
```

### 2. Claude Code CLIのインストール

```bash
# Node.jsが必要
npm install -g @anthropic-ai/claude-code
```

### 3. 環境変数の設定

`.env.sample`を`.env`にコピーして設定：

```bash
cp .env.sample .env
```

`.env`ファイルを編集して以下を設定：

```bash
# 既存の設定
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token-here
CLAUDE_USER_ID=XXXXXXX

# Socket Mode用のApp-level Token
SLACK_APP_TOKEN=xapp-your-app-token-here
```

### 4. Slack App設定の更新

#### Socket Modeの有効化
1. Slack App管理画面にアクセス
2. 左側メニューから「Socket Mode」を選択
3. Socket Modeを有効化

#### App-level Tokenの生成
1. 「App Token」セクションに移動
2. 新しいApp-level Tokenを生成
3. Scope: `connections:write`を追加
4. 生成されたxapp-トークンを`.env`に設定

#### Event Subscriptionsの設定
1. 「Event Subscriptions」ページで以下を確認：
   - `app_mention` イベント
   - `message.channels` イベント（必要に応じて）

### 5. 実行

```bash
python3 slack_monitor.py
```
