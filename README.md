# OmniPrompt Gateway (OPG)

Lightweight Python CLI for multi-model LLM interactions. Supports OpenAI, Anthropic, Ollama, and LM Studio APIs with MCP filesystem tools. Single executable deployment with no dependencies.

## Quick Start

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and add your API keys
4. Run: `python opg.py`

## Features

- Multiple LLM support: OpenAI GPT-4/3.5, Anthropic Claude, Ollama, LM Studio
- Model Context Protocol (MCP) integration for filesystem access
- Rich terminal UI with markdown rendering
- Seamless model switching within conversations
- System prompt customization
- Lightweight design with minimal dependencies

## Commands

- `/help` - Show all commands
- `/models` - List available models  
- `/new [model]` - Start new conversation
- `/clear` - Clear current conversation
- `/prompt [text]` - Set system prompt
- `/quit` - Exit

## Configuration

Edit `.env` file:

```bash
# Required for cloud models
OPENAI_API_KEY=your-key-here
ANTHROPIC_API_KEY=your-key-here

# Optional: MCP filesystem access
ENABLE_MCP=true
MCP_FILESYSTEM_PATH=C:/safe/directory
```

### .env File Location

OPG looks for `.env` in two places (in order):
1. **Current working directory** - where you run the command from
2. **Next to the executable** - same folder as `opg.exe` or `opg.py`

This allows flexible usage:
- **Portable**: Keep `.env` with `opg.exe` for consistent settings
- **Project-specific**: Put different `.env` files in different project folders
- **Multiple configs**: Run OPG from different directories to use different API keys or settings

## Requirements

- Python 3.8+ (development only)
- Node.js (optional, for MCP features)
- No runtime dependencies for standalone executable

## License

MIT
