#!/usr/bin/env python
"""
OmniPrompt Gateway (OPG) - Multi-model LLM interface with MCP support
"""
from __future__ import annotations
import os, sys, json, textwrap, requests
from dataclasses import dataclass, asdict, field
from typing import Callable, Dict, List, Optional
from datetime import datetime

try:
	from dotenv import load_dotenv
	# Try loading .env from current directory first, then from exe directory
	env_loaded = False
	if os.path.exists('.env'):
		# Use .env in current working directory
		load_dotenv()
		env_loaded = True
		# Uncomment for debugging: print(f"Loaded .env from current directory: {os.getcwd()}")
	else:
		# Look for .env next to the executable
		if getattr(sys, 'frozen', False):
			# Running as compiled executable
			app_dir = os.path.dirname(sys.executable)
		else:
			# Running as script
			app_dir = os.path.dirname(os.path.abspath(__file__))
		
		env_path = os.path.join(app_dir, '.env')
		if os.path.exists(env_path):
			load_dotenv(env_path)
			env_loaded = True
			# Uncomment for debugging: print(f"Loaded .env from: {app_dir}")
		
	if not env_loaded:
		print(f"Note: No .env file found")
		print(f"Searched in: current directory and {app_dir if 'app_dir' in locals() else 'application directory'}")
		print(f"Create .env from .env.example and add your API keys")
except ImportError:
	print("Error: python-dotenv not installed. Please run: pip install python-dotenv")
	sys.exit(1)

# MCP imports with fallback
try:
	from robust_mcp_wrapper import RobustMCPClient as SimpleMCPClient, integrate_mcp_simple, extract_and_execute_tool_calls
	MCP_AVAILABLE = True
except ImportError:
	print("Warning: MCP module not found. MCP features will be disabled.")
	MCP_AVAILABLE = False
	SimpleMCPClient = None
	integrate_mcp_simple = None
	extract_and_execute_tool_calls = None

from rich.console import Console
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.prompt import Prompt
console = Console()

__version__ = "1.0.1"
__app_name__ = "OmniPrompt Gateway"

# ---------- configuration ----------
@dataclass
class Message:
	role: str
	content: str

@dataclass
class Model:
	name: str                 # Friendly display name
	endpoint: str             # Full URL of API endpoint
	model_id: str             # Model identifier
	auth_env: str | None      # Env-var that holds API key
	auth_header: str          # Header format (e.g., "Bearer {}", "x-api-key: {}")
	system_prompt: str        # Default system prompt
	adapter: Callable        # Function that does POST + parses JSON
	max_tokens: int = 4096    # Max tokens in response
	temperature: float = 0.7  # Default temperature

@dataclass
class Conversation:
	model_name: str
	messages: List[Message] = field(default_factory=list)
	created_at: datetime = field(default_factory=datetime.now)

# --- adapters for different APIs -------------------------------------------
def openai_chat(model: Model, messages: List[Message]) -> str:
	"""Adapter for OpenAI API (also works for OpenAI-compatible APIs)"""
	headers = {
		"Content-Type": "application/json"
	}
	if model.auth_env:
		api_key = os.getenv(model.auth_env)
		if api_key:
			headers["Authorization"] = model.auth_header.format(api_key)
	
	payload = {
		"model": model.model_id,
		"messages": [asdict(msg) for msg in messages],
		"temperature": model.temperature,
		"max_tokens": model.max_tokens
	}
	
	try:
		r = requests.post(model.endpoint, headers=headers, json=payload, timeout=60)
		r.raise_for_status()
		return r.json()["choices"][0]["message"]["content"].strip()
	except requests.exceptions.RequestException as e:
		raise Exception(f"API request failed: {str(e)}")
	except (KeyError, IndexError) as e:
		raise Exception(f"Unexpected response format: {str(e)}")

def claude_chat(model: Model, messages: List[Message]) -> str:
	"""Adapter for Claude API (Anthropic)"""
	headers = {
		"Content-Type": "application/json",
		"anthropic-version": "2023-06-01"
	}
	if model.auth_env:
		api_key = os.getenv(model.auth_env)
		if api_key:
			headers["x-api-key"] = api_key
	
	# Convert messages to Claude format
	claude_messages = []
	for msg in messages:
		if msg.role != "system":  # Claude handles system prompts differently
			claude_messages.append({
				"role": msg.role,
				"content": msg.content
			})
	
	# Extract system prompt if present
	system_prompt = next((msg.content for msg in messages if msg.role == "system"), model.system_prompt)
	
	payload = {
		"model": model.model_id,
		"messages": claude_messages,
		"max_tokens": model.max_tokens,
		"temperature": model.temperature,
		"system": system_prompt
	}
	
	try:
		r = requests.post(model.endpoint, headers=headers, json=payload, timeout=60)
		r.raise_for_status()
		return r.json()["content"][0]["text"].strip()
	except requests.exceptions.RequestException as e:
		raise Exception(f"API request failed: {str(e)}")
	except (KeyError, IndexError) as e:
		raise Exception(f"Unexpected response format: {str(e)}")

def ollama_chat(model: Model, messages: List[Message]) -> str:
	"""Adapter for Ollama local models"""
	payload = {
		"model": model.model_id,
		"messages": [asdict(msg) for msg in messages],
		"options": {
			"temperature": model.temperature,
			"num_predict": model.max_tokens
		},
		"stream": False
	}
	
	try:
		r = requests.post(model.endpoint, json=payload, timeout=120)
		r.raise_for_status()
		return r.json()["message"]["content"].strip()
	except requests.exceptions.RequestException as e:
		raise Exception(f"API request failed: {str(e)}")
	except (KeyError, IndexError) as e:
		raise Exception(f"Unexpected response format: {str(e)}")

# --- Model configurations -----------------------------------------------
def get_models() -> Dict[str, Model]:
	"""Load model configurations from environment or use defaults"""
	models = {}
	
	# Get the generic system prompt (used as fallback for all models)
	generic_prompt = os.getenv("GENERIC_SYSTEM_PROMPT", "You are a helpful assistant.")
	
	# OpenAI GPT-4
	if os.getenv("OPENAI_API_KEY"):
		models["gpt4"] = Model(
			name="gpt4",
			endpoint=os.getenv("OPENAI_API_ENDPOINT", "https://api.openai.com/v1/chat/completions"),
			model_id=os.getenv("OPENAI_MODEL", "gpt-4"),
			auth_env="OPENAI_API_KEY",
			auth_header="Bearer {}",
			system_prompt=os.getenv("GPT4_SYSTEM_PROMPT", generic_prompt),
			adapter=openai_chat,
			temperature=float(os.getenv("GPT4_TEMPERATURE", "0.7"))
		)
		
		# GPT-3.5
		models["gpt3.5"] = Model(
			name="gpt3.5",
			endpoint=os.getenv("OPENAI_API_ENDPOINT", "https://api.openai.com/v1/chat/completions"),
			model_id="gpt-3.5-turbo",
			auth_env="OPENAI_API_KEY",
			auth_header="Bearer {}",
			system_prompt=os.getenv("GPT35_SYSTEM_PROMPT", generic_prompt),
			adapter=openai_chat,
			temperature=float(os.getenv("GPT35_TEMPERATURE", "0.7"))
		)
	
	# Claude
	if os.getenv("ANTHROPIC_API_KEY"):
		models["claude"] = Model(
			name="claude",
			endpoint=os.getenv("CLAUDE_API_ENDPOINT", "https://api.anthropic.com/v1/messages"),
			model_id=os.getenv("CLAUDE_MODEL", "claude-3-sonnet-20240229"),
			auth_env="ANTHROPIC_API_KEY",
			auth_header="x-api-key: {}",
			system_prompt=os.getenv("CLAUDE_SYSTEM_PROMPT", generic_prompt),
			adapter=claude_chat,
			temperature=float(os.getenv("CLAUDE_TEMPERATURE", "0.7"))
		)
	
	# LM Studio (OpenAI-compatible local server)
	lm_studio_endpoint = os.getenv("LM_STUDIO_ENDPOINT", "http://localhost:1234/v1/chat/completions")
	# Check if LM Studio is running by trying to connect
	try:
		r = requests.get(lm_studio_endpoint.replace("/chat/completions", "/models"), timeout=1)
		if r.status_code == 200:
			models["lmstudio"] = Model(
				name="lmstudio",
				endpoint=lm_studio_endpoint,
				model_id=os.getenv("LM_STUDIO_MODEL", "local-model"),
				auth_env=None,
				auth_header="",
				system_prompt=os.getenv("LM_STUDIO_SYSTEM_PROMPT", generic_prompt),
				adapter=openai_chat,  # LM Studio uses OpenAI-compatible API
				temperature=float(os.getenv("LM_STUDIO_TEMPERATURE", "0.7"))
			)
	except:
		pass  # LM Studio not running
	
	# Ollama (local)
	ollama_endpoint = os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434/api/chat")
	ollama_model = os.getenv("OLLAMA_MODEL", "llama2")
	models["ollama"] = Model(
		name="ollama",
		endpoint=ollama_endpoint,
		model_id=ollama_model,
		auth_env=None,
		auth_header="",
		system_prompt=os.getenv("OLLAMA_SYSTEM_PROMPT", generic_prompt),
		adapter=ollama_chat,
		temperature=float(os.getenv("OLLAMA_TEMPERATURE", "0.7"))
	)
	
	return models

# ---------- CLI functions ----------
class LLMChat:
	def __init__(self):
		self.models = get_models()
		self.current_conversation: Optional[Conversation] = None
		self.conversations: List[Conversation] = []
		# Store custom default prompt (starts with env value or default)
		self.default_system_prompt = os.getenv("GENERIC_SYSTEM_PROMPT", "You are a helpful assistant.")
		
	def start_new_conversation(self, model_name: str, custom_prompt: Optional[str] = None):
		"""Start a new conversation with the specified model"""
		if model_name not in self.models:
			raise ValueError(f"Unknown model: {model_name}")
			
		model = self.models[model_name]
		self.current_conversation = Conversation(model_name=model_name)
		
		# Use custom prompt if provided, otherwise use model's default
		prompt = custom_prompt if custom_prompt else model.system_prompt
		
		# Add system prompt as first message
		self.current_conversation.messages.append(
			Message(role="system", content=prompt)
		)
		self.conversations.append(self.current_conversation)
		
	def add_message(self, role: str, content: str):
		"""Add a message to the current conversation"""
		if not self.current_conversation:
			raise ValueError("No active conversation")
			
		self.current_conversation.messages.append(Message(role=role, content=content))
		
	def get_response(self, user_input: str) -> str:
		"""Get response from the current model"""
		if not self.current_conversation:
			raise ValueError("No active conversation")
			
		# Add user message
		self.add_message("user", user_input)
		
		# Get model and adapter
		model = self.models[self.current_conversation.model_name]
		
		# Get response
		try:
			response = model.adapter(model, self.current_conversation.messages)
			# Add assistant response to conversation
			self.add_message("assistant", response)
			return response
		except Exception as e:
			# Remove the user message if there was an error
			self.current_conversation.messages.pop()
			raise
			
	def list_models(self) -> List[str]:
		"""List available models"""
		return list(self.models.keys())
		
	def get_conversation_history(self) -> str:
		"""Get formatted conversation history"""
		if not self.current_conversation:
			return "No active conversation"
			
		history = []
		for msg in self.current_conversation.messages:
			if msg.role != "system":  # Skip system prompts in display
				history.append(f"{msg.role.upper()}: {msg.content}")
				
		return "\n\n".join(history)
	
	def update_system_prompt(self, new_prompt: str):
		"""Update the system prompt for the current conversation"""
		if not self.current_conversation:
			raise ValueError("No active conversation")
		
		# Find and update the system message
		for i, msg in enumerate(self.current_conversation.messages):
			if msg.role == "system":
				self.current_conversation.messages[i] = Message(role="system", content=new_prompt)
				return
		
		# If no system message found, add one at the beginning
		self.current_conversation.messages.insert(0, Message(role="system", content=new_prompt))
	
	def get_current_system_prompt(self) -> Optional[str]:
		"""Get the current conversation's system prompt"""
		if not self.current_conversation:
			return None
		
		for msg in self.current_conversation.messages:
			if msg.role == "system":
				return msg.content
		
		return None

def print_formatted_response(response: str):
	"""Print response with markdown formatting"""
	# Use rich to render markdown
	markdown = Markdown(response)
	console.print(Panel(markdown, title="[bold blue]Response[/bold blue]", border_style="blue"))

def print_help(chat=None, mcp_client=None):
	"""Print help information in a nice table"""
	table = Table(title=f"{__app_name__} Commands", show_header=True, header_style="bold cyan")
	table.add_column("Command", style="bold green", width=25)
	table.add_column("Description", style="white")
	
	# Add commands to table
	table.add_row("/help", "Show this help menu")
	table.add_row("/models", "List available models")
	table.add_row("/new [model]", "Start new conversation with specified model")
	table.add_row("/history", "Show conversation history")
	table.add_row("/clear", "Clear current conversation (keeps model)")
	table.add_row("/prompt [text]", "Set system prompt for current conversation")
	table.add_row("/prompt+", "Set multi-line system prompt (end with 'END')")
	table.add_row("/setdefault [text]", "Set default system prompt for new conversations")
	table.add_row("/setdefault+", "Set multi-line default prompt (end with 'END')")
	table.add_row("/loadprompt [file]", "Load system prompt from a text file")
	table.add_row("/showprompt", "Show current system prompt")
	table.add_row("/quit or /q", "Exit the program")

	if mcp_client:
		table.add_row("", "")  # Spacer
		table.add_row("[dim]MCP Tools[/dim]", "[dim]When MCP is enabled:[/dim]")
		table.add_row("", "LLMs can use filesystem tools")
		table.add_row("", "Look for ```mcp-tool blocks")
	
	console.print(table)
	console.print("\n[dim]Tip: For single-line prompts with line breaks, use \\\\n[/dim]")
	console.print("[dim]Any other input will be sent to the current model.[/dim]")

def main():
	"""Main CLI loop"""
	chat = LLMChat()

	# Initialize MCP if enabled
	mcp_client = None
	if MCP_AVAILABLE and SimpleMCPClient is not None and os.getenv('ENABLE_MCP', 'true').lower() == 'true':
		try:
			mcp_client = SimpleMCPClient()
			fs_path = os.getenv('MCP_FILESYSTEM_PATH', os.getcwd())
			mcp_client.add_filesystem_server(fs_path)
			if integrate_mcp_simple is not None:
				integrate_mcp_simple(chat, mcp_client)
			console.print("[green]✓ MCP filesystem tools enabled![/green]")
		except Exception as e:
			console.print(f"[yellow]Warning: MCP initialization failed: {e}[/yellow]")
			console.print("[dim]Continuing without MCP support...[/dim]")
			mcp_client = None
	
	# Check if we have at least one configured model
	if not chat.models:
		console.print(f"[bold red]Error:[/bold red] No models configured. Please set up API keys in your .env file.")
		sys.exit(1)
	
	console.print(f"[bold cyan]🚀 {__app_name__} v{__version__}[/bold cyan] - Type /help for commands")
	console.print(f"Available models: [bold green]{', '.join(chat.list_models())}[/bold green]")
	
	# Start with first available model
	default_model = list(chat.models.keys())[0]
	console.print(f"\n[dim]Starting conversation with [bold]{default_model}[/bold][/dim]")
	chat.start_new_conversation(default_model)
	
	while True:
		try:
			user_input = input("\n> ").strip()
			
			if not user_input:
				continue
				
			# Handle commands
			if user_input.startswith("/"):
				parts = user_input.split(maxsplit=1)
				command = parts[0].lower()
				args = parts[1] if len(parts) > 1 else ""
				
				if command in ["/quit", "/q", "/exit"]:
					console.print("[yellow]Goodbye![/yellow]")
					break
					
				elif command == "/help":
					print_help(chat, mcp_client)
					
				elif command == "/models":
					table = Table(title="Available Models", show_header=True, header_style="bold cyan")
					table.add_column("Model", style="bold green")
					table.add_column("Status", style="yellow")
					
					for model_name in chat.list_models():
						status = "Active" if chat.current_conversation and chat.current_conversation.model_name == model_name else "Available"
						table.add_row(model_name, status)
					
					console.print(table)
					
				elif command == "/new":
					if not args:
						console.print("[red]Please specify a model.[/red] Available: " + ", ".join(chat.list_models()))
					elif args not in chat.models:
						console.print(f"[red]Unknown model: {args}.[/red] Available: " + ", ".join(chat.list_models()))
					else:
						chat.start_new_conversation(args)
						console.print(f"[green]Started new conversation with {args}[/green]")
						
				elif command == "/history":
					console.print("\n[bold cyan]--- Conversation History ---[/bold cyan]")
					if chat.current_conversation and len(chat.current_conversation.messages) > 1:
						for msg in chat.current_conversation.messages:
							if msg.role != "system":
								if msg.role == "user":
									console.print(f"\n[bold green]USER:[/bold green] {msg.content}")
								else:
									console.print(f"\n[bold blue]ASSISTANT:[/bold blue] {msg.content}")
					else:
						console.print("[dim]No messages yet[/dim]")
					console.print("[bold cyan]--- End of History ---[/bold cyan]")
					
				elif command == "/clear":
					if chat.current_conversation:
						model_name = chat.current_conversation.model_name
						chat.start_new_conversation(model_name)
						console.print(f"[green]Cleared conversation. Starting fresh with {model_name}[/green]")
					else:
						console.print("[red]No active conversation to clear[/red]")
						
				elif command == "/prompt":
					if not args:
						console.print("[red]Please provide a system prompt.[/red] Usage: /prompt Your prompt here")
						console.print("[dim]For multi-line prompts, use /prompt+ to enter multi-line mode[/dim]")
					elif not chat.current_conversation:
						console.print("[red]No active conversation. Start one with /new [model][/red]")
					else:
						# Replace \n with actual newlines
						args = args.replace('\\n', '\n')
						chat.update_system_prompt(args)
						console.print("[green]Updated system prompt for current conversation[/green]")
						
				elif command == "/prompt+":
					if not chat.current_conversation:
						console.print("[red]No active conversation. Start one with /new [model][/red]")
					else:
						console.print("[cyan]Enter multi-line prompt (type 'END' on a new line when done):[/cyan]")
						lines = []
						while True:
							line = input()
							if line.strip() == 'END':
								break
							lines.append(line)
						multi_prompt = '\n'.join(lines)
						chat.update_system_prompt(multi_prompt)
						console.print("[green]Updated system prompt for current conversation[/green]")
						
				elif command == "/setdefault":
					if not args:
						console.print("[red]Please provide a system prompt.[/red] Usage: /setdefault Your default prompt here")
						console.print("[dim]For multi-line prompts, use /setdefault+ to enter multi-line mode[/dim]")
					else:
						# Replace \n with actual newlines
						args = args.replace('\\n', '\n')
						chat.default_system_prompt = args
						# Also update all models' default prompts
						for model in chat.models.values():
							model.system_prompt = args
						console.print("[green]Updated default system prompt for all new conversations[/green]")
						
				elif command == "/setdefault+":
					console.print("[cyan]Enter multi-line default prompt (type 'END' on a new line when done):[/cyan]")
					lines = []
					while True:
						line = input()
						if line.strip() == 'END':
							break
						lines.append(line)
					multi_prompt = '\n'.join(lines)
					chat.default_system_prompt = multi_prompt
					# Also update all models' default prompts
					for model in chat.models.values():
						model.system_prompt = multi_prompt
					console.print("[green]Updated default system prompt for all new conversations[/green]")
						
				elif command == "/showprompt":
					prompt = chat.get_current_system_prompt()
					if prompt:
						console.print(Panel(prompt, title="[bold cyan]Current System Prompt[/bold cyan]", border_style="cyan"))
					else:
						console.print("[red]No active conversation[/red]")
						
				elif command == "/loadprompt":		
					if not args:
						console.print("[red]Please provide a file path.[/red] Usage: /loadprompt path/to/prompt.txt")
					elif not chat.current_conversation:
						console.print("[red]No active conversation. Start one with /new [model][/red]")
					else:
						try:
							with open(args.strip(), 'r', encoding='utf-8') as f:
								prompt_content = f.read()
							chat.update_system_prompt(prompt_content)
							console.print(f"[green]Loaded system prompt from {args.strip()}[/green]")
						except FileNotFoundError:
							console.print(f"[red]Error: File not found: {args.strip()}[/red]")
						except Exception as e:
							console.print(f"[red]Error reading file: {e}[/red]")
					
				else:
					console.print(f"[red]Unknown command: {command}.[/red] Type /help for commands.")
					
			else:
				# Send to model
				if not chat.current_conversation:
					console.print("[red]No active conversation. Use /new [model] to start.[/red]")
					continue
					
				console.print("\n[dim]Thinking...[/dim]", end="")
				try:
					response = chat.get_response(user_input)
					print("\r" + " " * 20 + "\r", end="")  # Clear "Thinking..."
					print_formatted_response(response)
					
					# Check for MCP tool calls
					if mcp_client and extract_and_execute_tool_calls is not None:
						tool_results = extract_and_execute_tool_calls(response, mcp_client)
						if tool_results:
							console.print()  # Add spacing
							for result in tool_results:
								console.print(Panel(
									result, 
									title="[bold green]MCP Tool Result[/bold green]", 
									border_style="green"
								))
				
				except Exception as e:
					print("\r" + " " * 20 + "\r", end="")  # Clear "Thinking..."
					console.print(f"\n[bold red]❌ Error:[/bold red] {e}")
					
		except KeyboardInterrupt:
			console.print("\n\n[yellow]Use /quit to exit properly.[/yellow]")
		except EOFError:
			console.print("\n[yellow]Goodbye![/yellow]")
			break

	if mcp_client:
		mcp_client.cleanup()

if __name__ == "__main__":
	# Check for missing API keys
	models = get_models()
	if not models:
		console.print(f"[bold red]Error:[/bold red] No models available. Please configure at least one API key in your .env file.")
		console.print("\n[dim]Example .env file:[/dim]")
		console.print("[dim]OPENAI_API_KEY=your-openai-key-here[/dim]")
		console.print("[dim]ANTHROPIC_API_KEY=your-claude-key-here[/dim]")
		sys.exit(1)
	
	missing_keys = []
	for name, model in models.items():
		if model.auth_env and not os.getenv(model.auth_env):
			missing_keys.append(f"{name} ({model.auth_env})")
	
	if missing_keys:
		console.print(f"[yellow]Warning: Missing API keys for:[/yellow] {', '.join(missing_keys)}")
		console.print("[dim]These models will not be available.[/dim]\n")
	
	main()
