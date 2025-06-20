"""
CLI formatting utilities for OmniPrompt Gateway
"""
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.align import Align
from rich.text import Text
from typing import Dict, List, Optional

from core import mcp_manager

console = Console()


def create_status_display(current_model: Optional[str] = None) -> Panel:
	"""Create a status display panel showing current model"""
	if current_model:
		status_text = Text(f"Current Model: {current_model}", style="bold green")
	else:
		status_text = Text("No Active Model", style="bold red")
	
	return Panel(
		Align.center(status_text),
		title="Status",
		border_style="cyan",
		height=3
	)


def print_grouped_models(models_dict, current_model: Optional[str] = None):
	"""Print models grouped by provider with proper indentation"""
	# Group models by provider
	provider_models = {}
	for model_name, model_obj in models_dict.items():
		provider = model_obj.provider
		if provider not in provider_models:
			provider_models[provider] = []
		provider_models[provider].append(model_name)
	
	console.print("\n[bold cyan]Available Models by Provider:[/bold cyan]")
	
	for provider, models in provider_models.items():
		# Print provider name
		console.print(f"[bold yellow]{provider}:[/bold yellow]")
		
		# Print each model indented
		for model in models:
			if model == current_model:
				console.print(f"    [bold green]• {model}[/bold green] [dim](current)[/dim]")
			else:
				console.print(f"    • {model}")
	console.print()


def print_formatted_response(response: str):
	"""Print response with markdown formatting"""
	# Use rich to render markdown
	markdown = Markdown(response)
	console.print(Panel(markdown, title="[bold blue]Response[/bold blue]", border_style="blue"))


def print_help(app_name: str, chat=None, mcp_client=None):
	"""Print help information in a nice table"""
	table = Table(title=f"{app_name} Commands", show_header=True, header_style="bold cyan")
	table.add_column("Command", style="bold green", width=25)
	table.add_column("Description", style="white")
	
	# Add commands to table
	table.add_row("/help", "Show this help menu")
	table.add_row("/models", "List available models grouped by provider")
	table.add_row("/new [model]", "Start new conversation with specified model")
	table.add_row("/history", "Show conversation history")
	table.add_row("/clear", "Clear current conversation (keeps model)")
	table.add_row("/prompt [text]", "Set system prompt for current conversation")
	table.add_row("/prompt+", "Set multi-line system prompt (end with 'END')")
	table.add_row("/setdefault [text]", "Set default system prompt for new conversations")
	table.add_row("/setdefault+", "Set multi-line default prompt (end with 'END')")
	table.add_row("/loadprompt [file]", "Load system prompt from a text file")
	table.add_row("/showprompt", "Show current system prompt")
	table.add_row("/changemodels", "Change available models for any provider")
	table.add_row("/api", "Switch between Chat/Responses API (OpenAI only)")
	table.add_row("/status [on/off]", "Toggle model name in prompt (model> vs >)")
	table.add_row("/quit or /q", "Exit the program")

	if mcp_manager.is_available():
		table.add_row("", "")  # Spacer
		table.add_row("[dim]MCP Tools[/dim]", "[dim]When MCP is enabled:[/dim]")
		table.add_row("", "LLMs can use filesystem tools")
		table.add_row("", "Look for ```mcp-tool blocks")
	
	console.print(table)
	console.print("\n[dim]Tip: For single-line prompts with line breaks, use \\\\n[/dim]")
	console.print("[dim]Any other input will be sent to the current model.[/dim]")


def print_models_table(models: list[str], current_model: str | None = None):
	"""Print available models in a table format"""
	table = Table(title="Available Models", show_header=True, header_style="bold cyan")
	table.add_column("Model", style="bold green")
	table.add_column("Status", style="yellow")
	
	for model_name in models:
		status = "Active" if current_model and current_model == model_name else "Available"
		table.add_row(model_name, status)
	
	console.print(table)


def print_conversation_history(chat):
	"""Print conversation history in a formatted way"""
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


def print_error(message: str):
	"""Print an error message"""
	console.print(f"[bold red]❌ Error:[/bold red] {message}")


def print_warning(message: str):
	"""Print a warning message"""
	console.print(f"[yellow]Warning:[/yellow] {message}")


def print_success(message: str):
	"""Print a success message"""
	console.print(f"[green]{message}[/green]")


def print_info(message: str):
	"""Print an info message"""
	console.print(f"[cyan]{message}[/cyan]")


def print_mcp_tool_result(result: str):
	"""Print MCP tool execution result"""
	console.print(Panel(
		result, 
		title="[bold green]MCP Tool Result[/bold green]", 
		border_style="green"
	))



