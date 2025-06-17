"""
Main CLI interface for OmniPrompt Gateway
"""
import sys
from core import LLMChat, mcp_manager
from .commands import CommandHandler
from .formatting import (
	console, print_formatted_response, print_mcp_tool_result,
	print_error, print_success, print_info, print_grouped_models
)


class CLIInterface:
	"""Main CLI interface for OmniPrompt Gateway"""
	
	def __init__(self, app_name: str, version: str):
		self.app_name = app_name
		self.version = version
		self.chat = LLMChat()
		self.command_handler = CommandHandler(self.chat, app_name, self)
		self.mcp_client = None
		self.show_model_in_prompt = True  # Flag to control model display in prompt
	
	def initialize(self):
		"""Initialize the CLI interface"""
		# Initialize MCP using the new manager
		self.mcp_client = mcp_manager.initialize_mcp(self.chat)
		
		# Check if we have at least one configured model
		if not self.chat.models:
			print_error("No models configured. Please set up API keys in your .env file.")
			sys.exit(1)
		
		# Welcome message
		console.print(f"[bold cyan]🚀 {self.app_name} v{self.version}[/bold cyan] - Type /help for commands")
		
		# Start with first available model
		default_model = list(self.chat.models.keys())[0]
		console.print(f"\n[dim]Starting conversation with [/dim][bold green]{default_model}[/bold green]")
		self.chat.start_new_conversation(default_model)
				# Show models grouped by provider
		print_grouped_models(self.chat.models, default_model)
	
	def run(self):
		"""Run the main CLI loop"""
		while True:
			try:
				# Create prompt based on status setting
				if self.show_model_in_prompt and self.chat.current_conversation:
					current_model = self.chat.current_conversation.model_name
					prompt_text = f"{current_model}> "
				else:
					prompt_text = "> "
				
				user_input = input(prompt_text).strip()
				
				if not user_input:
					continue
					
				# Handle commands
				if user_input.startswith("/"):
					should_quit = self.command_handler.handle_command(user_input)
					if should_quit:
						break
				else:
					# Send to model
					self._handle_user_message(user_input)
					
			except KeyboardInterrupt:
				console.print("\n\n[yellow]Use /quit to exit properly.[/yellow]")
			except EOFError:
				console.print("\n[yellow]Goodbye![/yellow]")
				break
				# Cleanup
		self.cleanup()
	
	def _handle_user_message(self, user_input: str):
		"""Handle a user message (non-command)"""
		if not self.chat.current_conversation:
			print_error("No active conversation. Use /new [model] to start.")
			return
			
		console.print("\n[dim]Thinking...[/dim]", end="")
		try:
			response = self.chat.get_response(user_input)
			print("\r" + " " * 20 + "\r", end="")  # Clear "Thinking..."
			print_formatted_response(response)
			
			# Check for MCP tool calls
			tool_results = mcp_manager.extract_and_execute_tools(response)
			if tool_results:
				console.print()  # Add spacing
				for result in tool_results:
					print_mcp_tool_result(result)
		
		except Exception as e:
			print("\r" + " " * 20 + "\r", end="")  # Clear "Thinking..."
			print_error(str(e))
	
	def cleanup(self):
		"""Cleanup resources"""
		mcp_manager.cleanup()
	
	def toggle_status_display(self) -> bool:
		"""Toggle the model display in prompt and return new state"""
		self.show_model_in_prompt = not self.show_model_in_prompt
		return self.show_model_in_prompt
