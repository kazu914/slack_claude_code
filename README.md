# 🤖 Slack Claude Code Integration

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Slack](https://img.shields.io/badge/Slack-Socket%20Mode-brightgreen.svg)](https://api.slack.com/apis/connections/socket)
[![Claude Code SDK](https://img.shields.io/badge/Claude%20Code-SDK-purple.svg)](https://claude.ai/code)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Slack Socket Mode integration with Claude Code Python SDK for real-time AI-powered assistance**

## 🚀 Features

- **🔄 Real-time Integration**: Seamless connection between Slack and Claude Code using Socket Mode
- **🎯 Channel-specific Configuration**: Different Claude Code settings per Slack channel
- **📊 Smart Tool Output Management**: Intelligent batching of tool notifications to reduce noise
- **🔒 Security First**: Secure token-based authentication with environment variable management
- **⚡ High Performance**: Asynchronous processing with comprehensive error handling
- **🛠️ Developer Friendly**: Full type annotations, code quality tools integration

## 📋 Prerequisites

- **Python 3.11+**
- **Slack workspace** with admin permissions
- **Claude Code CLI** installed
- **uv** package manager (recommended) or pip

## 🛠️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/slack_claude_code.git
cd slack_claude_code
```

### 2. Install Dependencies

#### Using uv (Recommended)
```bash
# Install dependencies with automatic virtual environment management
uv sync
```

#### Using pip
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install slack_bolt claude-code-sdk requests
```

### 3. Install Claude Code CLI

```bash
npm install -g @anthropic-ai/claude-code
```

## ⚙️ Configuration

### 1. Environment Variables

Copy the sample environment file and configure your tokens:

```bash
cp .env.sample .env
```

Edit `.env` with your actual tokens:

```bash
# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token-here
SLACK_APP_TOKEN=xapp-your-app-token-here
CLAUDE_USER_ID=your-claude-user-id
```

### 2. Slack App Setup

#### Enable Socket Mode
1. Go to your Slack App management page
2. Navigate to "Socket Mode" in the sidebar
3. Enable Socket Mode

#### Generate App-level Token
1. Go to "App Token" section
2. Create a new App-level token
3. Add scope: `connections:write`
4. Copy the generated `xapp-` token to your `.env` file

#### Configure Event Subscriptions
Ensure these events are subscribed:
- `app_mention`
- `message.channels` (if needed)

### 3. Channel Configuration

Create your channel configuration file:

```bash
cp channel_configs.json.sample channel_configs.json
```

Example configuration:

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

## 🚀 Usage

### Starting the Service

```bash
# Using uv
uv run python slack_monitor.py

# Using pip
python slack_monitor.py
```

### Interacting in Slack

1. **Mention the bot** in any configured channel
2. **Give instructions** in natural language
3. **Monitor progress** with intelligent tool output batching
4. **Receive results** directly in the Slack thread

Example:
```
@Claude Help me analyze this codebase and suggest improvements
```

## 📁 Project Structure

```
slack_claude_code/
├── slack_monitor.py              # Main Socket Mode monitoring script
├── claude_code_message_notifier.py  # Smart tool output management
├── message_utils.py              # Message processing utilities
├── system_prompt.md              # Claude Code system prompt template
├── channel_configs.json          # Channel-specific configurations
├── pyproject.toml               # Project dependencies and settings
├── SLACK_SETUP.md               # Detailed setup instructions
└── CLAUDE.md                    # Claude Code integration guide
```

## 🔧 Development

### Code Quality Tools

```bash
# Type checking
uv run mypy slack_monitor.py

# Code formatting and linting
uv run ruff check .
uv run ruff format .

# Mandatory check after modifications
uv tool run ruff check ./slack_monitor.py --fix
```

### Key Components

#### SlackSocketMonitor Class
- Socket Mode event handling
- Asynchronous message processing
- Claude Code SDK integration

#### ClaudeCodeMessageNotifier Class
- Intelligent tool output batching
- Reduces Slack notification noise
- Configurable notification thresholds

## 🎨 Smart Features

### Tool Output Management
- **Batch Notifications**: Tools usage summarized every 10 operations
- **Mixed Content Handling**: Immediate display of user-facing content
- **Noise Reduction**: Eliminates repetitive tool execution messages

### Channel Flexibility
- **Per-channel Settings**: Different Claude Code configurations per Slack channel
- **Permission Modes**: Choose between bypass or request permissions
- **Tool Restrictions**: Allow/disallow specific tools per channel

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with proper type annotations
4. Run code quality checks (`uv tool run ruff check . --fix`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙋‍♀️ Support

- 📖 **Documentation**: Check `SLACK_SETUP.md` for detailed setup instructions
- 🐛 **Issues**: Report bugs via GitHub Issues
- 💡 **Feature Requests**: Suggest new features via GitHub Issues

## 🏆 Acknowledgments

- Built with [Claude Code SDK](https://claude.ai/code)
- Powered by [Slack Bolt for Python](https://slack.dev/bolt-python/)
- Uses [uv](https://github.com/astral-sh/uv) for fast Python package management

---

**Made with ❤️ for seamless AI-human collaboration**