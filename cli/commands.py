"""
CLI command handling for OmniPrompt Gateway
"""
from rich.panel import Panel

from core import LLMChat, mcp_manager
from config.models import get_available_providers, set_provider_models, get_models
from .formatting import (
	console, print_help, print_models_table, print_conversation_history,
	print_error, print_success, print_info, print_grouped_models
)


class CommandHandler:
	"""Handles CLI command processing"""
	
	def __init__(self, chat: LLMChat, app_name: str, interface=None):
		self.chat = chat
		self.app_name = app_name
		self.interface = interface
	
	def handle_command(self, user_input: str) -> bool:
		"""
		Handle a CLI command
		
		Args:
			user_input: The user input starting with '/'
			
		Returns:
			bool: True if the command was 'quit', False otherwise
		"""
		parts = user_input.split(maxsplit=1)
		command = parts[0].lower()
		args = parts[1] if len(parts) > 1 else ""
		
		if command in ["/quit", "/q", "/exit"]:
			console.print("[yellow]Goodbye![/yellow]")
			return True
			
		elif command == "/help":
			print_help(self.app_name)
			
		elif command == "/models":
			current_model = self.chat.current_conversation.model_name if self.chat.current_conversation else None
			print_grouped_models(self.chat.models, current_model)
			
		elif command == "/new":
			self._handle_new_command(args)
			
		elif command == "/history":
			print_conversation_history(self.chat)
			
		elif command == "/clear":
			self._handle_clear_command()
			
		elif command == "/prompt":
			self._handle_prompt_command(args)
			
		elif command == "/prompt+":
			self._handle_multiline_prompt_command()
			
		elif command == "/setdefault":
			self._handle_setdefault_command(args)
			
		elif command == "/setdefault+":
			self._handle_multiline_setdefault_command()
			
		elif command == "/showprompt":
			self._handle_showprompt_command()
			
		elif command == "/loadprompt":
			self._handle_loadprompt_command(args)
			
		elif command == "/changemodels":
			self._handle_changemodels_command()
			
		elif command == "/status":
			self._handle_status_command(args)
			
		else:
			print_error(f"Unknown command: {command}. Type /help for commands.")
		
		return False
	
	def _handle_new_command(self, args: str):
		"""Handle /new command"""
		if not args:
			print_error("Please specify a model. Available: " + ", ".join(self.chat.list_models()))
		elif args not in self.chat.models:
			print_error(f"Unknown model: {args}. Available: " + ", ".join(self.chat.list_models()))
		else:
			self.chat.start_new_conversation(args)
			print_success(f"Started new conversation with {args}")
	
	def _handle_clear_command(self):
		"""Handle /clear command"""
		if self.chat.current_conversation:
			model_name = self.chat.current_conversation.model_name
			self.chat.start_new_conversation(model_name)
			print_success(f"Cleared conversation. Starting fresh with {model_name}")
		else:
			print_error("No active conversation to clear")
	
	def _handle_prompt_command(self, args: str):
		"""Handle /prompt command"""
		if not args:
			print_error("Please provide a system prompt. Usage: /prompt Your prompt here")
			print_info("For multi-line prompts, use /prompt+ to enter multi-line mode")
		elif not self.chat.current_conversation:
			print_error("No active conversation. Start one with /new [model]")
		else:
			# Replace \n with actual newlines
			args = args.replace('\\n', '\n')
			self.chat.update_system_prompt(args)
			print_success("Updated system prompt for current conversation")
	
	def _handle_multiline_prompt_command(self):
		"""Handle /prompt+ command"""
		if not self.chat.current_conversation:
			print_error("No active conversation. Start one with /new [model]")
		else:
			print_info("Enter multi-line prompt (type 'END' on a new line when done):")
			lines = []
			while True:
				line = input()
				if line.strip() == 'END':
					break
				lines.append(line)
			multi_prompt = '\n'.join(lines)
			self.chat.update_system_prompt(multi_prompt)
			print_success("Updated system prompt for current conversation")
	
	def _handle_setdefault_command(self, args: str):
		"""Handle /setdefault command"""
		if not args:
			print_error("Please provide a system prompt. Usage: /setdefault Your default prompt here")
			print_info("For multi-line prompts, use /setdefault+ to enter multi-line mode")
		else:
			# Replace \n with actual newlines
			args = args.replace('\\n', '\n')
			self.chat.default_system_prompt = args
			# Also update all models' default prompts
			for model in self.chat.models.values():
				model.system_prompt = args
			print_success("Updated default system prompt for all new conversations")
	
	def _handle_multiline_setdefault_command(self):
		"""Handle /setdefault+ command"""
		print_info("Enter multi-line default prompt (type 'END' on a new line when done):")
		lines = []
		while True:
			line = input()
			if line.strip() == 'END':
				break
			lines.append(line)
		multi_prompt = '\n'.join(lines)
		self.chat.default_system_prompt = multi_prompt
		# Also update all models' default prompts
		for model in self.chat.models.values():
			model.system_prompt = multi_prompt
		print_success("Updated default system prompt for all new conversations")
	
	def _handle_showprompt_command(self):
		"""Handle /showprompt command"""
		prompt = self.chat.get_current_system_prompt()
		if prompt:
			console.print(Panel(prompt, title="[bold cyan]Current System Prompt[/bold cyan]", border_style="cyan"))
		else:
			print_error("No active conversation")
	
	def _handle_loadprompt_command(self, args: str):
		"""Handle /loadprompt command"""
		if not args:
			print_error("Please provide a file path. Usage: /loadprompt path/to/prompt.txt")
		elif not self.chat.current_conversation:
			print_error("No active conversation. Start one with /new [model]")
		else:
			try:
				with open(args.strip(), 'r', encoding='utf-8') as f:
					prompt_content = f.read()
				self.chat.update_system_prompt(prompt_content)
				print_success(f"Loaded system prompt from {args.strip()}")
			except FileNotFoundError:
				print_error(f"File not found: {args.strip()}")
			except Exception as e:
				print_error(f"Error reading file: {e}")
	
	def _handle_changemodels_command(self):
		"""Handle /changemodels command"""
		# Get available providers
		providers = get_available_providers()
		
		# Display provider options
		print_info("Available providers:")
		for i, (provider, available, models) in enumerate(providers, 1):
			status = "[green]Available[/green]" if available else "[red]Not configured[/red]"
			console.print(f"{i}. {provider} - {status}")
			if available and models:
				console.print(f"   Current models: {', '.join(models)}")
		
		console.print("\nSelect a provider (number) or 'cancel' to exit:")
		choice = input("> ").strip()
		
		if choice.lower() == 'cancel':
			print_info("Cancelled model configuration")
			return
		
		try:
			provider_idx = int(choice) - 1
			if 0 <= provider_idx < len(providers):
				provider_name, available, current_models = providers[provider_idx]
				
				if not available:
					print_error(f"Provider '{provider_name}' is not configured. Please set up the API key first.")
					return
				
				# Ask for model list
				console.print(f"\nEnter model IDs for {provider_name} (comma-separated):")
				if current_models:
					console.print(f"Current: {', '.join(current_models)}")
				console.print("Examples:")
				
				if provider_name == "openai":
					console.print("  gpt-3.5-turbo, gpt-4, gpt-4o")
				elif provider_name == "anthropic":
					console.print("  claude-3-opus-20240229, claude-3-sonnet-20240229")
				elif provider_name == "local-lmstudio":
					console.print("  Model names as shown in LM Studio")
				elif provider_name == "local-ollama":
					console.print("  llama2, mistral, codellama")
				
				model_input = input("> ").strip()
				
				if model_input:
					new_models = [m.strip() for m in model_input.split(",") if m.strip()]
					if new_models:
						# Update provider models
						set_provider_models(provider_name, new_models)
						
						# Reload models in chat
						self.chat.models = get_models()
						
						# Check if current conversation's model is still available
						if (self.chat.current_conversation and 
							self.chat.current_conversation.model_name not in self.chat.models):
							print_info(f"Current model '{self.chat.current_conversation.model_name}' is no longer available.")
							# Start with first available model
							if self.chat.models:
								new_model = list(self.chat.models.keys())[0]
								self.chat.start_new_conversation(new_model)
								print_info(f"Switched to '{new_model}'")
						
						print_success(f"Updated {provider_name} models: {', '.join(new_models)}")
						print_info("Changes will persist for this session. Update .env file to make permanent.")
					else:
						print_error("No models specified")
				else:
					print_info("No changes made")
			else:
				print_error("Invalid selection")
		except ValueError:
			print_error("Please enter a valid number")

	def _handle_status_command(self, args: str):
		"""Handle /status command to toggle status display"""
		if not self.interface:
			print_error("Status control not available")
			return
		
		if args.lower() in ["off", "hide", "disable"]:
			self.interface.show_model_in_prompt = False
			print_success("Status display disabled. Prompt will show: > ")
		elif args.lower() in ["on", "show", "enable"]:
			self.interface.show_model_in_prompt = True
			print_success("Status display enabled. Prompt will show: model> ")
		else:
			# Show current status and toggle
			current_state = self.interface.toggle_status_display()
			if current_state:
				print_success("Status display enabled. Prompt will show: model> ")
			else:
				print_success("Status display disabled. Prompt will show: > ")
