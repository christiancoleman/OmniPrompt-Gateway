"""
CLI command handling for OmniPrompt Gateway
"""
from rich.panel import Panel

from core import LLMChat, mcp_manager
from .formatting import (
	console, print_help, print_models_table, print_conversation_history,
	print_error, print_success, print_info
)


class CommandHandler:
	"""Handles CLI command processing"""
	
	def __init__(self, chat: LLMChat, app_name: str):
		self.chat = chat
		self.app_name = app_name
	
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
			print_models_table(self.chat.list_models(), current_model)
			
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
