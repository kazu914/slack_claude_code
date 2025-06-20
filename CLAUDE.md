# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Essential Commands

### Development Workflow
```bash
# Install dependencies (creates/manages virtual environment automatically)
uv sync

# Environment setup
cp .env.sample .env
# Edit .env file to configure tokens

# Run the application
uv run python slack_monitor.py
```

### Code Quality (Primary Workflow)
```bash
# Lint and format (most frequently used)
uv run ruff check .
uv run ruff format .

# Type checking
uv run mypy slack_monitor.py

# Critical: Always run after any slack_monitor.py modifications
uv run ruff check ./slack_monitor.py --fix
```

## Project Architecture

### Core System
This project implements a real-time Slack monitoring system using Socket Mode integration with Claude Code Python SDK. The system receives Slack message events via Socket Mode and processes user instructions through Claude Code SDK.

### Key Components
- `slack_monitor.py`: Main Socket Mode monitoring script
- `system_prompt.md`: Claude Code system prompt configuration
- `channel_configs.json`: Channel-specific Claude Code settings
- `pyproject.toml`: UV project configuration file (Python dependency management)
- `uv.lock`: UV dependency lock file
- `SLACK_SETUP.md`: Setup instructions
- `.env.sample`: Environment variable template (actual `.env` not in repository)

### Processing Flow
1. Receive message events from Slack
2. Confirm user instructions and send initial response
3. Process user instructions using Claude Code SDK
4. Return processing results to Slack thread

## Code Standards

### Python Conventions
- Follow ruff configuration for all code formatting and linting
- Use type hints consistently
- Maintain async/await patterns for Socket Mode operations
- Write English-only comments and docstrings

### Critical Requirements
- **Always run ruff after any code changes**
- **Type check with mypy before commits**
- **Test Socket Mode integration after modifications**

## Configuration Management

### Environment Variables
- `SLACK_BOT_TOKEN`: Slack Bot User OAuth Token (xoxb-)
- `SLACK_APP_TOKEN`: Slack App-level Token (xapp-)
- `CLAUDE_USER_ID`: Claude User ID for SDK operations

### Channel-Specific Settings
The `channel_configs.json` file allows different Claude Code configurations per Slack channel:

#### Required Settings
- `cwd`: Working directory path
- `permission_mode`: Either `bypassPermissions` or `requestPermissions`

#### Optional Settings
- `allowed_tools`: List of permitted tools (e.g., `["Bash", "Read", "Write"]`)
- `max_thinking_tokens`: Maximum thinking tokens (default: 8000)
- `append_system_prompt`: Additional system prompt text
- `mcp_tools`: MCP tools list
- `continue_conversation`: Conversation continuation setting
- `max_turns`: Maximum conversation turns
- `disallowed_tools`: Prohibited tools list
- `model`: Claude model specification

### Claude Code Integration Settings
- Permission mode: `bypassPermissions`
- Communication language: As specified in user config
- Progress reporting: Enabled
- Working directory: Configurable at runtime
- System prompt: Dynamically loaded from `system_prompt.md`
- Channel management: Configured via `channel_configs.json`

## Project-Specific Instructions

### When Modifying slack_monitor.py
1. Always run `uv run ruff check ./slack_monitor.py --fix` after changes
2. Verify Socket Mode connection still works
3. Test message processing flow
4. Check error handling for API rate limits

### When Updating Dependencies
1. Use `uv add <package>` for new dependencies
2. Run `uv sync` to update lock file
3. Test application startup after dependency changes

### When Working with Slack Integration
- Socket Mode requires both bot token and app token
- Test in development Slack workspace first
- Monitor for rate limiting and connection stability
- Ensure proper error handling for network issues