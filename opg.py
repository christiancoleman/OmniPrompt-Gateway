#!/usr/bin/env python
"""
OmniPrompt Gateway (OPG) - Multi-model LLM interface with MCP support
"""
from __future__ import annotations
import sys

# Import configuration
from config import load_environment, get_models, validate_model_config

# Import CLI interface
from cli import CLIInterface

from rich.console import Console
console = Console()

__version__ = "1.0.2"
__app_name__ = "OmniPrompt Gateway"

# Load environment configuration
load_environment()


def main():
	"""Main entry point"""
	# Initialize and run CLI
	cli = CLIInterface(__app_name__, __version__)
	cli.initialize()
	cli.run()


if __name__ == "__main__":
	# Load and validate models
	models = get_models()
	missing_keys, warnings = validate_model_config(models)
	
	# Handle configuration errors
	if not models:
		console.print(f"[bold red]Error:[/bold red] No models available. Please configure at least one API key in your .env file.")
		console.print("\n[dim]Example .env file:[/dim]")
		console.print("[dim]OPENAI_API_KEY=your-openai-key-here[/dim]")
		console.print("[dim]ANTHROPIC_API_KEY=your-claude-key-here[/dim]")
		sys.exit(1)
	
	# Show warnings for missing API keys
	if missing_keys:
		console.print(f"[yellow]Warning: Missing API keys for:[/yellow] {', '.join(missing_keys)}")
		console.print("[dim]These models will not be available.[/dim]\n")
	
	main()
