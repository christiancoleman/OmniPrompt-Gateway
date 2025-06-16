# LLM Helper - Command Line Chat Interface

A simple command-line tool for maintaining conversations with various LLMs including OpenAI GPT, Claude, LM Studio, and local Ollama models.

## Features

- ✅ Maintains conversation history/context throughout the session
- ✅ Supports multiple LLM providers (OpenAI, Claude, LM Studio, Ollama)
- ✅ Configuration via `.env` file
- ✅ Easy model switching mid-conversation
- ✅ Works with Python 3.6+
- ✅ Multi-line prompt support
- ✅ Load prompts from files
- ✅ Customizable system prompts per model or globally
- ✅ Rich markdown rendering for formatted responses
- ✅ Beautiful tables and colored output

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env` and add your API keys:
   ```bash
   cp .env.example .env
   # Edit .env with your favorite editor
   ```

3. Run the program:
   ```bash
   python main.py
   ```

## Usage

### Commands

- `/help` - Show available commands
- `/models` - List available models
- `/new [model]` - Start a new conversation with specified model (e.g., `/new claude`)
- `/history` - Show the current conversation history
- `/clear` - Clear the current conversation but keep the same model
- `/prompt [text]` - Set system prompt for current conversation
- `/prompt+` - Enter multi-line prompt mode (end with 'END' on a new line)
- `/setdefault [text]` - Set default system prompt for all new conversations
- `/setdefault+` - Enter multi-line default prompt mode (end with 'END')
- `/loadprompt [file]` - Load system prompt from a text file
- `/showprompt` - Display the current conversation's system prompt
- `/quit` or `/q` - Exit the program

### Example Session

```
> Hello, can you help me with Python?
[Assistant responds with Python help]

> /new claude
Started new conversation with claude

> What's the difference between a list and tuple?
[Claude responds with explanation]

> /history
[Shows entire conversation]

> /prompt You are an expert Python developer. Be concise but thorough.
Updated system prompt for current conversation

> /setdefault You are a helpful AI assistant specializing in software development.
Updated default system prompt for all new conversations

> /prompt+ 
Enter multi-line prompt (type 'END' on a new line when done):
You are an expert Python developer.
Always:
- Write clean, efficient code
- Include helpful comments
- Follow PEP 8 standards
END
Updated system prompt for current conversation
```

## Supported Models

### Cloud Models
- **OpenAI**: GPT-4, GPT-3.5 (requires API key)
- **Claude**: Claude 3 Opus/Sonnet/Haiku (requires API key)

### Local Models
- **LM Studio**: Any model running in LM Studio (auto-detected)
- **Ollama**: Any model installed in Ollama

LM Studio will be automatically detected if it's running on the default port (1234). Just start LM Studio with a model loaded, and it will appear in your available models.

## Configuration

The `.env` file supports the following options:

### Required
- `OPENAI_API_KEY` - Your OpenAI API key
- `ANTHROPIC_API_KEY` - Your Claude API key

### Optional
- `OPENAI_MODEL` - GPT model to use (default: gpt-4)
- `CLAUDE_MODEL` - Claude model to use (default: claude-3-sonnet-20240229)
- `GENERIC_SYSTEM_PROMPT` - Default system prompt for all models (unless overridden)
- `GPT4_SYSTEM_PROMPT` - Custom system prompt for GPT-4 (overrides generic)
- `GPT35_SYSTEM_PROMPT` - Custom system prompt for GPT-3.5 (overrides generic)
- `CLAUDE_SYSTEM_PROMPT` - Custom system prompt for Claude (overrides generic)
- `OLLAMA_SYSTEM_PROMPT` - Custom system prompt for Ollama (overrides generic)
- `LM_STUDIO_ENDPOINT` - LM Studio API endpoint (default: http://localhost:1234/v1/chat/completions)
- `LM_STUDIO_MODEL` - Model name in LM Studio (default: local-model)
- `LM_STUDIO_SYSTEM_PROMPT` - Custom prompt for LM Studio (overrides generic)
- `GPT4_TEMPERATURE` - Temperature for GPT-4 (0.0-1.0)
- `CLAUDE_TEMPERATURE` - Temperature for Claude (0.0-1.0)
- `LM_STUDIO_TEMPERATURE` - Temperature for LM Studio (0.0-1.0)

## Multi-line Prompts

You can use multi-line prompts in several ways:

1. **Using `\n` in commands**: `/prompt You are an expert.\nAlways be concise.\nUse examples.`

2. **Multi-line mode**: Use `/prompt+` or `/setdefault+` to enter multiple lines:
   ```
   > /prompt+
   Enter multi-line prompt (type 'END' on a new line when done):
   You are a Python expert.
   Always follow best practices.
   Be thorough but concise.
   END
   ```

3. **Loading from file**: `/loadprompt C:\prompts\salesforce-expert.txt`

4. **In `.env` file**: Use actual line breaks in your `.env` file

### Sample Prompts

The `prompts/` directory includes example prompt files:
- `salesforce-architect.txt` - For Salesforce development
- `coding-expert.txt` - For general programming

Use them with: `/loadprompt prompts/salesforce-architect.txt`

## UI Features

### Rich Tables
All command outputs use formatted tables for better readability:
- `/help` - Commands displayed in a formatted table
- `/models` - Models shown with their current status

### Colored Output
- Commands and prompts use color coding
- Errors are highlighted in red
- Success messages in green
- System messages in cyan/blue

## Notes

- The program will work with whatever API keys you provide
- If you only have an OpenAI key, only GPT models will be available
- LM Studio and Ollama run locally and don't require API keys
- LM Studio is auto-detected when running on port 1234
- Conversation history is only maintained during the session (not saved to disk)
