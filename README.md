# OmniPrompt Gateway (OPG)

Multi-model LLM interface with MCP support. Access GPT-4, Claude, and local models through one command-line interface.

## Quick Start

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and add your API keys
4. Run: `python opg.py`

## Features

- **Multiple LLMs**: OpenAI GPT-4/3.5, Anthropic Claude, Ollama, LM Studio
- **MCP Tools**: File system access when enabled
- **Rich Terminal UI**: Markdown rendering and syntax highlighting
- **Conversation Management**: Switch models, clear history, save prompts

## Commands

- `/help` - Show all commands
- `/models` - List available models  
- `/new [model]` - Start new conversation
- `/clear` - Clear current conversation
- `/quit` - Exit

## Configuration

Edit `.env` file:

```bash
# Required
OPENAI_API_KEY=your-key-here
ANTHROPIC_API_KEY=your-key-here

# Optional MCP
ENABLE_MCP=true
MCP_FILESYSTEM_PATH=C:/safe/directory
```

## Building Executable

To create a standalone executable (not included in repo):

1. Create `build.py` with this content:
```python
import subprocess
import sys

subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"])
subprocess.run([
    "pyinstaller",
    "--onefile",
    "--name", "opg",
    "--add-data", "robust_mcp_wrapper.py;.",
    "--hidden-import", "robust_mcp_wrapper",
    "opg.py"
])
```

2. Run: `python build.py`
3. Find executable in `dist/opg.exe`
4. Deploy with `.env.example`

## Requirements

- Python 3.8+
- Node.js (for MCP features)

## License

MIT
